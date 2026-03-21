from mcp.server.fastmcp import FastMCP
from fastapi import FastAPI
import uvicorn
import os
from elasticsearch import Elasticsearch
import psycopg2
from psycopg2.extras import RealDictCursor

# Configuración de PostgreSQL (Transactional DB)
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = os.getenv("PG_PORT", "5432")
PG_USER = os.getenv("PG_USER", "user")
PG_PASSWORD = os.getenv("PG_PASSWORD", "password")
PG_DB = os.getenv("PG_DB", "payment_db")

# Configuración de Elasticsearch (Kibana)
# Se toman de variables de entorno, o usa defaults locales para no fallar el arranque
ES_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
ES_API_KEY = os.getenv("ELASTICSEARCH_API_KEY", "")

# Inicializar cliente de Elastic
if ES_API_KEY:
    es_client = Elasticsearch(ES_URL, api_key=ES_API_KEY)
else:
    es_client = Elasticsearch(ES_URL) # Sin auth para desarrollo local


# Inicializar un servidor FastMCP estándar
# FastMCP es el wrapper recomendado para crear servidores MCP rápidamente en Python
mcp = FastMCP("sarip-mcp-gateway")

@mcp.tool()
def get_transaction_lifecycle(transaction_id: str) -> dict:
    """
    Obtiene los montos, fechas, proveedor y estado actual de la transacción consultando directamente la Core DB (PostgreSQL).
    """
    print(f"[Core DB] Consultando PostgreSQL por transacción: {transaction_id}")
    
    try:
        # 1. Establecer conexión
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            user=PG_USER,
            password=PG_PASSWORD,
            dbname=PG_DB
        )
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # 2. Consultar la tabla de transacciones
        query = "SELECT id, amount, currency, status, service_id, customer_reference, created_at, updated_at FROM transactions WHERE id = %s"
        cur.execute(query, (transaction_id,))
        record = cur.fetchone()
        
        cur.close()
        conn.close()
        
        # 3. Formatear respuesta para el LLM
        if record:
            # Convertir fechas a strings para que el dict sea serializable por JSON
            record['created_at'] = record['created_at'].isoformat() if record.get('created_at') else None
            record['updated_at'] = record['updated_at'].isoformat() if record.get('updated_at') else None
            # Convertir UUID a String
            record['id'] = str(record['id'])
            return dict(record)
        else:
            return {"error": f"Transacción {transaction_id} no encontrada en la base de datos."}
            
    except Exception as e:
        print(f"[!] Error consultando PostgreSQL: {e}")
        return {"error": "Fallo al conectar con la Base de Datos Core.", "detalles": str(e)}

@mcp.tool()
def query_application_logs(trace_id: str, time_window_start: str, time_window_end: str) -> dict:
    """
    Ejecuta una búsqueda en Elasticsearch (Kibana) para encontrar excepciones de microservicios asimilables a una operación caída.
    """
    print(f"[Elasticsearch] Buscando logs para trace: {trace_id} entre {time_window_start} y {time_window_end}")
    
    # Armar Query DSL para buscar el Trace ID y filtrar solo ERRORES
    query = {
        "query": {
            "bool": {
                "must": [
                    { "term": { "trace_id.keyword": trace_id } },
                    { "match": { "level_name": "ERROR" } }
                ],
                "filter": [
                    {
                        "range": {
                            "@timestamp": {
                                "gte": time_window_start,
                                "lte": time_window_end
                            }
                        }
                    }
                ]
            }
        },
        "size": 5 # Limitar carga cognitiva del LLM
    }
    
    try:
        # Ejecutar búsqueda en el índice de logs (por defecto logstash-* o logs-*)
        response = es_client.search(index="service-payment-logs-*", body=query)
        
        hits = response.get("hits", {}).get("hits", [])
        
        if not hits:
            return {
                "trace_id": trace_id,
                "logs_found": 0,
                "exceptions": ["No se encontraron errores en Kibana para este Trace ID en la ventana de tiempo."]
            }
            
        # Extraer los mensajes de error reales
        excepciones_reales = []
        for hit in hits:
            source = hit.get("_source", {})
            message = source.get("message", "Error sin mensaje")
            stack = source.get("StackTrace", "")
            # Truncar stack a 3 líneas útiles
            short_stack = "\\n".join(stack.split("\\n")[:3])
            excepciones_reales.append(f"{message} \\nException: {short_stack}")
            
        return {
            "trace_id": trace_id,
            "logs_found": len(hits),
            "exceptions": excepciones_reales
        }
        
    except Exception as e:
        print(f"[!] Error consultando Elasticsearch: {e}")
        # Retorno seguro (Fallback) para que el Agente no colapse si Kibana está caído
        return {
            "trace_id": trace_id,
            "error": "Fallo al conectar con el cluster de Kibana",
            "detalles": str(e)
        }

@mcp.tool()
def search_playbook(company_id: str, error_code_or_symptom: str) -> str:
    """
    Realiza una búsqueda semántica en la base vectorial para obtener pasos estructurados de soporte (SOP) ante un error dado.
    """
    print(f"[RAG Mock] Buscando knowledge base para company {company_id} y error {error_code_or_symptom}")
    return "Playbook HINT: Verificar disponibilidad del API Gateway de la aseguradora. Accion recomendada: REJECT_AND_REVERSE."

if __name__ == "__main__":
    print("Iniciando SARIP MCP Gateway (FastMCP SSE)...")
    mcp.settings.port = 8081
    mcp.run(transport="sse")
