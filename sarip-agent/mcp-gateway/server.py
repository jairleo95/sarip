from mcp.server.fastmcp import FastMCP
from fastapi import FastAPI
import uvicorn

# Inicializar un servidor FastMCP estándar
# FastMCP es el wrapper recomendado para crear servidores MCP rápidamente en Python
mcp = FastMCP("sarip-mcp-gateway")

@mcp.tool()
def get_transaction_lifecycle(transaction_id: str) -> dict:
    """
    Obtiene los montos, fechas, cuentas involucradas y estados históricos (AUTHORIZED, SETTLED, etc.) de una transacción específica.
    """
    print(f"[Core DB Mock] Buscando transacción: {transaction_id}")
    return {
        "transaction_id": transaction_id,
        "status": "SETTLED",
        "amount": 150.00,
        "currency": "USD",
        "date": "2023-10-27T10:02:11Z"
    }

@mcp.tool()
def query_application_logs(trace_id: str, time_window_start: str, time_window_end: str) -> dict:
    """
    Ejecuta una búsqueda en Splunk u OpenSearch para encontrar excepciones de Java u OOM Kills asimilables a una operación caída.
    """
    print(f"[Splunk Mock] Buscando logs para trace: {trace_id} entre {time_window_start} y {time_window_end}")
    return {
        "trace_id": trace_id,
        "logs_found": 1,
        "exceptions": [
            "ConnectionReadTimeoutException in AguaCorpClient"
        ]
    }

@mcp.tool()
def search_playbook(company_id: str, error_code_or_symptom: str) -> str:
    """
    Realiza una búsqueda semántica en la base vectorial para obtener pasos estructurados de soporte (SOP) ante un error dado.
    """
    print(f"[RAG Mock] Buscando knowledge base para company {company_id} y error {error_code_or_symptom}")
    return "Playbook HINT: Verificar disponibilidad del API Gateway de la aseguradora. Accion recomendada: REJECT_AND_REVERSE."

# Mapear el servidor MCP dentro de una aplicación FastAPI
app = FastAPI(title="SARIP MCP Gateway", description="Gateway Seguro para tools de LangGraph")

@app.get("/health")
def health_check():
    return {"status": "UP", "component": "sarip-mcp-gateway"}

# FastMCP incluye un helper para montar el servidor de Server-Sent Events (SSE) en FastAPI
mcp.add_to_app(app)

if __name__ == "__main__":
    # Arrancar el servidor ASGI (FastAPI) exponiendo los endpoints de MCP
    print("Iniciando SARIP MCP Gateway (FastAPI + SSE)...")
    uvicorn.run("server:app", host="0.0.0.0", port=8080, reload=True)
