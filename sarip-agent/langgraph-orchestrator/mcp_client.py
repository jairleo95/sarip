import httpx
import json
import os
import psycopg2
from typing import Dict, Any

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8080")
ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")

class SimpleMCPClient:
    """
    Cliente Integrado para interactuar con PostgreSQL y Elasticsearch en vivo.
    Conecta LangGraph con el mundo real para el RCA iterativo.
    """
    
    @staticmethod
    def call_tool(tool_name: str, arguments: dict) -> dict:
        print(f"[MCP Client] Invocando Tool Segura remota: {tool_name} con args {arguments}")
        
        if tool_name == "get_transaction_lifecycle":
            trx_id = arguments.get("transaction_id", "")
            return SimpleMCPClient._query_postgres(trx_id)
            
        elif tool_name == "query_application_logs":
            trace_id = arguments.get("trace_id", "")
            # El ID que manda el router a logs suele tener prefijos.
            # Limpiemos para buscar el UUID o el recibo real.
            clean_search_term = trace_id.replace("trace-", "").replace("OP-", "").strip()
            return SimpleMCPClient._query_elasticsearch(clean_search_term)
            
        return {"error": f"Tool {tool_name} no encontrada o acceso denegado por RBAC."}
        
    @staticmethod
    def _query_postgres(transaction_id: str) -> dict:
        """Consulta directa a la base de datos transaccional usando psycopg2."""
        try:
            conn = psycopg2.connect(
                dbname="payment_db",
                user="user",
                password="password",
                host="localhost",
                port="5432"
            )
            cur = conn.cursor()
            
            # Buscar por UUID o por el Recibo Corto (receipt_number) o customer_reference, id
            query = """
                SELECT id, service_id, customer_reference, amount, currency, status, receipt_number, provider_endorsement, created_at, updated_at 
                FROM transactions 
                WHERE id::text = %s OR receipt_number = %s OR customer_reference = %s
            """
            cur.execute(query, (transaction_id, transaction_id, transaction_id))
            row = cur.fetchone()
            
            cur.close()
            conn.close()
            
            if row:
                return {
                    "transaction_id": str(row[0]),
                    "service_id": row[1],
                    "customer_reference": row[2],
                    "amount": float(row[3]),
                    "currency": row[4],
                    "status": row[5],
                    "receipt_number": row[6],
                    "provider_endorsement": row[7],
                    "timestamp": str(row[8]),
                    "updated_at": str(row[9]),
                    "source": "CORE_DB_READ_REPLICA"
                }
            else:
                return {"error": f"Transacción '{transaction_id}' no encontrada en PostgreSQL."}
                
        except Exception as e:
            return {"error": f"Error conectando a PostgreSQL: {e}"}

    @staticmethod
    def _query_elasticsearch(search_term: str) -> dict:
        """Busca excepciones o errores en el índice de logs en Elasticsearch."""
        try:
            # Buscar en el index global '*'
            query_url = f"{ELASTICSEARCH_URL}/_search"
            
            payload = {
                "query": {
                  "bool": {
                    "must": [
                      { "match": { "trace_id": search_term } },
                      { "match": { "level_name": "ERROR" } }
                    ]
                  }
                },
                "size": 5,
                "_source": ["message", "@timestamp", "level_name", "LoggerName", "StackTrace"]
            }
            
            # Timeout corto para no bloquear a LangGraph si ELK está caído
            response = httpx.post(query_url, json=payload, timeout=3.0)
            if response.status_code == 200:
                data = response.json()
                hits = data.get("hits", {}).get("hits", [])
                
                if hits:
                    exceptions = []
                    for h in hits:
                        src = h.get("_source", {})
                        msg = src.get("message", "")
                        ts = src.get("@timestamp", "")
                        logger = src.get("LoggerName", "")
                        stack = src.get("StackTrace", "")
                        # Limitar el stack trace a las primeras 3 líneas para no abrumar al LLM
                        short_stack = "\\n".join(stack.split("\\n")[:3])
                        exceptions.append(f"[{ts}] {logger}: {msg} \\nException: {short_stack}")
                        
                    return {
                        "logs_found": len(hits),
                        "exceptions": exceptions,
                        "source": "ELASTICSEARCH_API"
                    }
                else:
                    return {"logs_found": 0, "exceptions": [], "source": "ELASTICSEARCH_API", "message": "No error logs matching trace."}
            else:
                return {"error": f"Elasticsearch respondió con status: {response.status_code}"}
                
        except Exception as e:
            return {"error": f"Error consultando Elasticsearch: {e}"}
