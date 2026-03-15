import httpx
import json
import os
from typing import Dict, Any

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8080")

class SimpleMCPClient:
    """
    Cliente Ligero para interactuar con el FastMCP Server expuesto via HTTP/SSE.
    En una versión de producción avanzada, se usaría el `mcp.client` nativo con WebSockets/SSE persistentes.
    Para este MVP de 7 días, dado que FastAPI expone endpoints estáticos a veces, o podemos invocar directo.
    Nota: FastMCP envuelve las tools internamente. Para consumirlas fácil en este script sin el cliente asíncrono completo MCP,
    simularemos la llamada si el protocolo nativo es complejo de inicializar en CLI.
    """
    
    # En un entorno real MCP esto negocia Capabilities y lee .tools() asincronamente.
    # Por rapidez del MVP (Día 6) interactuaremos vía un wrapper simulado o llamada REST directa
    # si hubiésemos expuesto la Tool directamente en FastAPI. 
    # Aquí vamos a simular la respuesta del Gateway MCP para continuar el flujo de LangGraph sincrono.

    @staticmethod
    def call_tool(tool_name: str, arguments: dict) -> dict:
        print(f"[MCP Client] Invocando Tool Segura remota: {tool_name} con args {arguments}")
        
        # Simulación de respuesta estándar Gateway MCP
        if tool_name == "get_transaction_lifecycle":
            trx_id = arguments.get("transaction_id", "UNKNOWN")
            return {
                "transaction_id": trx_id,
                "status": "SETTLED",
                "amount": 150.00,
                "currency": "USD",
                "timestamp": "2023-10-27T10:02:11Z",
                "source": "CORE_DB_READ_REPLICA"
            }
            
        elif tool_name == "query_application_logs":
            return {
                "logs_found": 1,
                "exceptions": ["ConnectionReadTimeoutException in AguaCorpClient"],
                "source": "SPLUNK_API"
            }
            
        return {"error": f"Tool {tool_name} no encontrada o acceso denegado por RBAC."}
