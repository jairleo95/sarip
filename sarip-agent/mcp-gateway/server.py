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
            short_stack = "\n".join(stack.split("\n")[:3])
            excepciones_reales.append(f"{message} \nException: {short_stack}")
            
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

@mcp.tool()
def search_codebase(keyword: str) -> str:
    """
    Busca una palabra clave (ej. Nombre de Excepción) en el código fuente de Java del sistema transaccional usando grep.
    Retorna los archivos y líneas donde se encuentra.
    """
    import subprocess
    print(f"[L3 Tool] Buscando en código fuente: {keyword}")
    cwd = "/home/darkstar/Workspace/dev/service-payment/transactional-system"
    try:
        result = subprocess.run(
            ["grep", "-rnF", keyword, "src/main/java"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.stdout:
            # Limitar a las primeras 30 líneas para no desbordar el contexto del LLM
            lines = result.stdout.split("\\n")[:30]
            return "Hallazgos de código:\\n" + "\\n".join(lines)
        return "No se encontraron coincidencias en el código fuente de Java."
    except Exception as e:
        return f"Error al ejecutar search_codebase: {e}"

@mcp.tool()
def read_java_source_code(file_path: str, start_line: int, end_line: int) -> str:
    """
    Lee un rango de líneas de un archivo Java específico para entender la lógica de negocio.
    Ejemplo de file_path: src/main/java/com/bank/service/PaymentService.java
    """
    import os
    print(f"[L3 Tool] Leyendo archivo {file_path} líneas {start_line}-{end_line}")
    full_path = os.path.join("/home/darkstar/Workspace/dev/service-payment/transactional-system", file_path)
    
    if not os.path.exists(full_path):
        return f"Error: El archivo {file_path} no existe."
        
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        snippet = lines[max(0, start_line-1):end_line]
        return f"--- Código Fuente: {file_path} (Líneas {start_line}-{end_line}) ---\\n" + "".join(snippet)
    except Exception as e:
        return f"Error al leer el archivo: {e}"

@mcp.tool()
def execute_custom_sql(query: str) -> str:
    """
    Ejecuta una consulta SELECT personalizada (Read-Only) en la Base de Datos Core (PostgreSQL) para investigar anomalías transaccionales.
    """
    print(f"[L3 Tool] Ejecutando consulta SQL L3: {query}")
    if "INSERT" in query.upper() or "UPDATE" in query.upper() or "DELETE" in query.upper() or "DROP" in query.upper():
        return "Error de Seguridad: Solo se permiten consultas SELECT (Read-Only)."
        
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(query)
        rows = cur.fetchall()
        
        # Obtener nombres de columnas
        colnames = [desc[0] for desc in cur.description]
        conn.close()
        
        if not rows:
            return "La consulta se ejecutó con éxito pero no devolvió resultados."
            
        # Formatear como lista de diccionarios truncada
        result_list = []
        for row in rows[:15]: # Limitar a 15 filas
            result_list.append(dict(zip(colnames, row)))
            
        import json
        return json.dumps(result_list, indent=2, default=str)
    except Exception as e:
        return f"Database Error: {e}"

@mcp.tool()
def check_git_history(file_path: str) -> str:
    """
    Revisa el historial reciente de Git para un archivo específico, para ver si un despliegue reciente causó un error.
    """
    import subprocess
    print(f"[L3 Tool] Revisando Git History de: {file_path}")
    cwd = "/home/darkstar/Workspace/dev/service-payment/transactional-system"
    try:
        result = subprocess.run(
            ["git", "log", "-n", "3", "--oneline", file_path],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.stdout:
            return "Últimos commits que afectaron este archivo:\\n" + result.stdout
        return "No hay historial de Git disponible para este archivo o no está bajo control de versiones."
    except Exception as e:
        return f"Error al revisar historial de Git: {e}"

@mcp.tool()
def get_system_metrics() -> str:
    """
    Consulta las métricas de sistema (Uso de CPU y Conexiones Activas de DB) para detectar saturaciones de infraestructura simuladas.
    """
    print("[L3 Tool] Consultando métricas de Telemetría (Prometheus Mock)")
    # En un entorno real, esto iría contra el endpoint /api/v1/query de Prometheus
    # Retornamos un log simulado genérico para propósitos de L3 Analysis
    return '''
[Métricas Extraídas]
- CPU Usage de service-payment: 87% (Alerta de Saturación)
- Active DB Connections (PostgreSQL): 98/100 (Cerca del Límite de Pool)
- Latencia Media a Proveedores (P99): 5.2s
- Estado de los pods de Kubernetes: Todos Running.
'''

if __name__ == "__main__":
    print("Iniciando SARIP MCP Gateway (FastMCP SSE)...")
    mcp.settings.port = 8081
    mcp.run(transport="sse")
