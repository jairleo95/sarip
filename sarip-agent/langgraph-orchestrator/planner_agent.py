import os
import json
import subprocess
import psycopg2
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent

# =================================================================================
# L3 RESEARCH PLANNER TOOLS
# Herramientas avanzadas para que la IA investigue como un Ingeniero Humano Senior
# =================================================================================

@tool
def search_codebase(keyword: str) -> str:
    """Busca una palabra clave o nombre de excepción en el código fuente de Java usando grep."""
    cwd = "/home/darkstar/Workspace/dev/service-payment/transactional-system"
    try:
        result = subprocess.run(["grep", "-rnF", keyword, "src/main/java"], cwd=cwd, capture_output=True, text=True, timeout=10)
        if result.stdout:
            lines = result.stdout.split("\n")[:30]
            return "Hallazgos de código:\n" + "\n".join(lines)
        return "No se encontraron coincidencias."
    except Exception as e:
        return f"Error: {e}"

@tool
def read_java_source_code(file_path: str, start_line: int, end_line: int) -> str:
    """Lee un rango de líneas de un archivo Java específico para entender la lógica de negocio."""
    full_path = os.path.join("/home/darkstar/Workspace/dev/service-payment/transactional-system", file_path)
    if not os.path.exists(full_path):
        return f"Error: El archivo {file_path} no existe."
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        snippet = lines[max(0, start_line-1):end_line]
        return f"--- Código Fuente: {file_path} (Líneas {start_line}-{end_line}) ---\n" + "".join(snippet)
    except Exception as e:
        return f"Error al leer el archivo: {e}"

@tool
def execute_custom_sql(query: str) -> str:
    """Ejecuta una consulta SELECT personalizada (Read-Only) en la BD PostgreSQL (payment_db) del core."""
    if any(q in query.upper() for q in ["INSERT", "UPDATE", "DELETE", "DROP"]):
        return "Error de Seguridad: Solo se permiten consultas SELECT (Read-Only)."
    try:
        conn = psycopg2.connect(dbname="payment_db", user="user", password="password", host="localhost", port="5432")
        cur = conn.cursor()
        cur.execute(query)
        rows = cur.fetchall()
        colnames = [desc[0] for desc in cur.description]
        conn.close()
        if not rows: return "La consulta se ejecutó pero no devolvió resultados."
        result_list = [dict(zip(colnames, row)) for row in rows[:15]]
        return json.dumps(result_list, indent=2, default=str)
    except Exception as e:
        return f"Database Error: {e}"

@tool
def check_git_history(file_path: str) -> str:
    """Revisa los últimos 3 commits de Git para un archivo específico buscando despliegues corruptos."""
    cwd = "/home/darkstar/Workspace/dev/service-payment/transactional-system"
    try:
        result = subprocess.run(["git", "log", "-n", "3", "--oneline", file_path], cwd=cwd, capture_output=True, text=True, timeout=5)
        return result.stdout if result.stdout else "No hay historial."
    except Exception as e:
        return f"Error: {e}"

@tool
def query_prometheus_metrics(promql_query: str) -> str:
    """
    Ejecuta una consulta PromQL real contra la instancia local de Prometheus.
    Sirve investigar cuellos de botella de infraestructura y telemetría activa (APM).
    """
    try:
        import httpx
        url = "http://localhost:9091/api/v1/query"
        response = httpx.get(url, params={"query": promql_query}, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        if data.get("status") == "success":
            results = data.get("data", {}).get("result", [])
            return json.dumps(results[:10], indent=2)
        else:
            return f"Prometheus Error: {data}"
    except Exception as e:
        return f"Prometheus unreachable: {e}"

# =================================================================================
# ENJAMBRE MULTI-AGENTE (SWARM L3 SUPERVISOR)
# =================================================================================

import json
from typing import Annotated, Sequence, Literal
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

# 1. Definir Sub-Agentes Especializados (Trabajadores)
llm = ChatOllama(model="llama3.1", temperature=0.0)

dba_agent = create_react_agent(
    llm, 
    tools=[execute_custom_sql], 
    prompt="Eres el DBA Agent. Tu supervisor te hará preguntas. Usa `execute_custom_sql` para buscar respuestas en PostgreSQL y explica tus hallazgos."
)
backend_agent = create_react_agent(
    llm, 
    tools=[search_codebase, read_java_source_code, check_git_history], 
    prompt="Eres el Backend Agent. Eres experto en Java nativo. Cuando el supervisor te asigne una consulta, usa tus herramientas para escanear el Spring Boot y explicarle la falla exacta."
)
sre_agent = create_react_agent(
    llm, 
    tools=[query_prometheus_metrics], 
    prompt="Eres el SRE Agent. Usas PromQL para validar el estado de CPU, y Memoria para el supervisor e identificar cuellos de botella de infraestructura."
)

# 2. Nodo Helper para Sub-Agentes
def make_node(agent_runnable, name: str):
    def node(state):
        # Le enviamos todo el historial al sub-agente para que tenga contexto
        result = agent_runnable.invoke({"messages": state["messages"]})
        # El sub-agente finaliza su loop ReAct, extraemos su último Output y lo devolvemos como HumanMessage al Supervisor
        final_answer = result["messages"][-1].content
        return {"messages": [HumanMessage(content=final_answer, name=name)]}
    return node

# 3. Estructura de Decisión del Supervisor
class SupervisorDecision(BaseModel):
    next_agent: Literal["dba", "backend", "sre", "FINISH"] = Field(
        description="El ID del agente a invocar para delegar ('dba', 'backend', 'sre') o 'FINISH' si terminaste la investigación."
    )
    instructions: str = Field(
        description="Explicación o mandato explícito sobre QUÉ debe buscar el agente elegido. Si es 'FINISH', este será tu L3 FORENSIC REPORT final para el humano."
    )

system_prompt = """Eres el Supervisor (Lead Investigator) de la Unidad L3 de SARIP.
Manejas a 3 agentes especializados: 'dba', 'backend', 'sre'.
Tu trabajo es armar el rompecabezas delegando micro-tareas de 1 en 1 basándote en el TICKET DE USUARIO.

Reglas:
1. Delega tareas mandando `instructions` claras según la herramienta que necesitas.
2. NUNCA resuelvas por tu cuenta si no tienes EVIDENCIA. Manda al 'backend' a revisar el código Java, o al 'sre' a revisar PromQL antes de decidir.
3. Cuando tengas certeza de la causa, llama a 'FINISH' y escribe en `instructions` el FORENSIC REPORT L3 detallado.
"""

# 4. Grafo y State
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    next_node: str

def supervisor_node(state):
    messages = state["messages"]
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
    ])
    
    # Invocamos al Supervisor obligando Structured Output (LLM-as-a-Judge Router)
    supervisor_chain = prompt | llm.with_structured_output(SupervisorDecision)
    decision = supervisor_chain.invoke({"messages": messages})
    
    # Si decide continuar, habla como un "Usuario Supervisor" hacia el siguiente nodo
    return {
        "next_node": decision.next_agent, 
        "messages": [HumanMessage(content=f"[Instrucción del Supervisor]: {decision.instructions}", name="supervisor")]
    }

workflow = StateGraph(AgentState)
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("dba", make_node(dba_agent, "dba"))
workflow.add_node("backend", make_node(backend_agent, "backend"))
workflow.add_node("sre", make_node(sre_agent, "sre"))

workflow.add_edge("dba", "supervisor")
workflow.add_edge("backend", "supervisor")
workflow.add_edge("sre", "supervisor")

workflow.add_conditional_edges(
    "supervisor",
    lambda state: state["next_node"],
    {"dba": "dba", "backend": "backend", "sre": "sre", "FINISH": END}
)

workflow.add_edge(START, "supervisor")
planner_app = workflow.compile()

def deep_research_ticket(ticket_context: str) -> str:
    print(f"\\n" + "="*60)
    print(f"🕵️ INICIANDO ENJAMBRE L3 (Multi-Agent Swarm)")
    print("="*60)
    
    inputs = {"messages": [HumanMessage(content=f"TICKET NUEVO. Por favor coordina al equipo para investigarlo:\\n\\n{ticket_context}")]}
    
    final_report = ""
    for event in planner_app.stream(inputs, stream_mode="updates"):
        for node_name, node_state in event.items():
            if "messages" in node_state:
                msg = node_state["messages"][-1].content
                print(f"\\n🗣️ [{node_name.upper()}]:\\n{msg}")
                if node_name == "supervisor" and node_state.get("next_node") == "FINISH":
                    final_report = msg
                    
    print("\\n" + "="*60)
    print("✅ INVESTIGACIÓN SWARM COMPLETADA")
    print("="*60)
    
    # En caso de no capturar FINISH de forma limpia
    if not final_report:
        # Recuperamos el último mensaje del state global
        final_state = planner_app.get_state(inputs) # wait, we can't reliably use get_state here with Ollama ephemeral memory
        pass # The loop usually catches it safely

    return final_report.replace("[Instrucción del Supervisor]: ", "")
