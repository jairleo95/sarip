from typing import Dict, Any, List
from state import TicketState, AuditLog
from rag import rag_instance
import json
import os
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

# Cargar variables de entorno (API Keys)
load_dotenv()

# Schema Estructurado de Salida para el LLM del Router
class RouterDecision(BaseModel):
    operations: List[str] = Field(description="IDs de transacciones financieras encontradas (ej. OP-123, trxn-999). Vacío si no hay.")
    company_suspected: str = Field(description="Empresa de servicios aludida (ej. AguaCorp, Movistar, Claro). 'UNKNOWN' si no se detecta.")
    reasoning: str = Field(description="Explicación breve de 1 línea de por qué se extrajeron esos datos.")

class ClasificadorDecision(BaseModel):
    failure_mode: str = Field(description="El Pattern de Falla Oficial (ej: TIMEOUT_BUSINESS, BILL_NOT_FOUND, RECONCILIATION_MISMATCH) según el playbook.")
    timeline: List[str] = Field(description="Lista cronológica de 2-4 strings describiendo los saltos de tiempo (ej. '10:01: Pago iniciado', '10:02: Excepción en log detectada').")
    reasoning: str = Field(description="El razonamiento forense de por qué este contexto BD + Traces encaja con ese failure mode.")

class RcaDecision(BaseModel):
    recommended_action: str = Field(description="Acción en MAYÚSCULAS requerida (Ej. REJECT_AND_REVERSE_DEBIT, MANUAL_RECONCILIATION, IGNORE).")
    confidence_score: float = Field(description="Nivel matemático de confianza del dictamen entre 0.0 y 1.0.")
    requires_human_approval: bool = Field(description="Booleano True si el confidence es bajo (<0.9) o el Playbook lo exige.")
    executive_summary: str = Field(description="Un resumen gerencial de 2 líneas narrando qué pasó y qué debe suceder ahora.")

def _get_attr(state: Any, attr: str, default: Any = None) -> Any:
    """Helper para extraer atributos sin importar si el state llega como Pydantic Model o Dict."""
    if isinstance(state, dict):
        return state.get(attr, default)
    return getattr(state, attr, default)

def router_agent(state: TicketState) -> dict:
    """"
    Nodo 1: Router Agente (Triage Inicial)
    Analiza el ticket, consulta RAG para contexto y decide qué operaciones investigar utilizando LLM con Structured Output.
    """
    ticket_id = _get_attr(state, "ticket_id", "NO-ID")
    desc = _get_attr(state, "description", "")
    
    print(f"--- ROUTER AGENT: Analizando Ticket {ticket_id} ---")
    
    # 1. Recuperar contexto rápido (RAG) basado en la descripción
    rag_context = rag_instance.search_playbook(desc, n_results=1)
    
    # 2. Configurar LLM Ágil (Haiku o GPT-4o-mini según propuesta arquitectónica)
    # Por defecto usaremos OpenAI para Structured Outputs nativo.
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
    structured_llm = llm.with_structured_output(RouterDecision)
    
    # 3. Construir el Prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Eres el Router Inicial de SARIP, un sistema de pagos bancario. "
                   "Tu tarea es leer la queja del cliente y el extracto de los manuales (Knowledge Base). "
                   "Debes extraer estrictamente los IDs de las transacciones financieras (que suelen tener formato OP-XXX o numérico) "
                   "y adivinar la empresa de la que se quejan."),
        ("human", "Ticket de Usuario: {ticket}\n\nConocimiento RAG Encontrado:\n{rag_knowledge}")
    ])
    
    # 4. Invocar Inteligencia
    try:
        decision = structured_llm.invoke(prompt.format_messages(ticket=desc, rag_knowledge=rag_context))
        ops = decision.operations
        reasoning = f"Detector LLM: '{decision.reasoning}' (Empresa: {decision.company_suspected})"
        print(f"  > Inteligencia Ruta: {reasoning} | Ops Extraídas: {ops}")
        
    except Exception as e:
        print(f"  > Error en LLM Router: {e}. Aplicando Fallback...")
        ops = []
        reasoning = "Error de conexión con LLM, ruteo por defecto."
        
    audit = AuditLog(agent="router", action=f"ticket_analyzed: {reasoning}").model_dump()
    
    return {
        "operations": ops,
        "next_agent": "evidence_collector",
        "audit_trail": [audit]
    }

from mcp_client import SimpleMCPClient

class EvidenceDecision(BaseModel):
    needs_db_query: bool = Field(description="¿Necesita buscar el estado en la base de datos?")
    needs_logs_query: bool = Field(description="¿Necesita buscar excepciones en los logs (Splunk)?")
    reasoning: str = Field(description="Justificación")

def evidence_collector(state: TicketState) -> dict:
    """"
    Nodo 2: Evidence Collector
    Llama al MCP Gateway para traer DB y Logs.
    """
    ops = _get_attr(state, "operations", [])
    print(f"--- EVIDENCE COLLECTOR: Recopilando datos BD y Logs para: {ops} ---")
    
    db_context_gathered = {}
    trace_context_gathered = []
    
    # 1. Agente LLM decide dinámicamente qué tools necesita (simulado en MVP)
    # Por rapidez del MVP para cada 'op' consultamos DB y Logs.
    # En la versión final, un LLM (Claude Haiku) evalúa si necesita ambos o solo uno.
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    structured_llm = llm.with_structured_output(EvidenceDecision)
    
    for op in ops:
        print(f"  > Evaluando herramientas para {op}...")
        try:
            decision = structured_llm.invoke(f"Se debe investigar la operacion financiera {op}. ¿Qué logs y BD necesitas?")
            print(f"  > Decisión LLM Collector: DB={decision.needs_db_query}, Logs={decision.needs_logs_query}")
            
            # 2. Invocación Real-Life al MCP Server Proxy
            if decision.needs_db_query:
                db_data = SimpleMCPClient.call_tool("get_transaction_lifecycle", {"transaction_id": op})
                db_context_gathered[op] = db_data
                
            if decision.needs_logs_query:
                trace_data = SimpleMCPClient.call_tool("query_application_logs", {"trace_id": f"trace-{op}", "time_window_start": "now-1h", "time_window_end": "now"})
                trace_context_gathered.append(trace_data)
                
        except Exception as e:
            print(f"  > Error en LLM Collector para {op}: {e}")
    
    # 3. Empaquetar y Auditar
    audit_msg = f"Evidencia recopilada para {len(ops)} operaciones (DB y Logs)"
    audit = AuditLog(agent="evidence_collector", action=audit_msg).model_dump()
    
    return {
        "db_context": db_context_gathered,
        "trace_context": trace_context_gathered,
        "next_agent": "clasificador",
        "audit_trail": _get_attr(state, "audit_trail", []) + [audit] # Preservando historial
    }

def clasificador(state: TicketState) -> dict:
    """
    Nodo 3: Clasificador Cognitivo
    Analiza toda la evidencia extraída (DB + Traces) y consulta si encaja con un "Failure Mode" documentado.
    """
    print("--- CLASIFICADOR: Identificando Patrón de Falla usando RAG Knowledge ---")
    
    # 1. Extraer el contexto reunido
    ticket_desc = _get_attr(state, "description", "")
    db_ctx = _get_attr(state, "db_context", {})
    trace_ctx = _get_attr(state, "trace_context", [])
    
    # Convertir JSONs a String para el Prompt
    db_str = json.dumps(db_ctx, indent=2)
    trace_str = json.dumps(trace_ctx, indent=2)
    
    # 2. Re-consultar el Playbook (Opcional, en MVP sirve refrescar la memoria del modelo analítico)
    rag_context = rag_instance.search_playbook(ticket_desc, n_results=1)
    
    # 3. Prompt Engineering Avanzado (Cognición Forense)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Eres el Clasificador Cognitivo Forense L3 del Banco. "
                   "Se te entregará la queja del cliente, los registros finales de la Base de Datos Financiera, "
                   "y los Logs de Splunk de la infraestructura extraídos por el Agente Recolector.\n\n"
                   "INSTRUCCIONES:\n"
                   "1. Lee la Knowledge Base (Playbook).\n"
                   "2. Mapea la evidencia técnica contra los 'Failure Modes Conocidos' del Playbook.\n"
                   "3. Genera un Timeline cronológico de los eventos.\n"
                   "4. Determina categóricamente el `failure_mode` exacto."),
        ("human", "TICKET INICIAL:\n{ticket}\n\n"
                  "RECORDS BASE DE DATOS LOCALIZADOS:\n{db_data}\n\n"
                  "LOGS / EXCEPCIONES LOCALIZADAS:\n{trace_data}\n\n"
                  "PLAYBOOK DE PROCEDIMIENTO:\n{rag_knowledge}")
    ])
    
    # Aquí podríamos usar un modelo más caro (ej. Claude 3.5 Sonnet o GPT-4o) por la ventana de contexto
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    structured_llm = llm.with_structured_output(ClasificadorDecision)
    
    try:
        decision = structured_llm.invoke(prompt.format_messages(
            ticket=ticket_desc,
            db_data=db_str,
            trace_data=trace_str,
            rag_knowledge=rag_context
        ))
        
        failure_mode = decision.failure_mode
        timeline = decision.timeline
        print(f"  > Falla Detectada: {failure_mode}")
        print(f"  > Razonamiento: {decision.reasoning}")
        
    except Exception as e:
        print(f"  > Error en LLM Clasificador: {e}")
        failure_mode = "UNKNOWN_ERROR_REQUIRES_HUMAN"
        timeline = ["Error de IA al clasificar la evidencia."]
        decision = ClasificadorDecision(failure_mode=failure_mode, timeline=timeline, reasoning=str(e))

    audit = AuditLog(agent="clasificador", action=f"Falla clasificada como {failure_mode}").model_dump()
    
    return {
        "failure_mode": failure_mode,
        "timeline": timeline,
        "next_agent": "rca_reporter",
        "audit_trail": _get_attr(state, "audit_trail", []) + [audit]
    }
    
def rca_reporter(state: TicketState) -> dict:
    """
    Nodo 4: RCA Reporter & Juez Final
    Dicta resolución (Actionable Item), establece puntuación de confianza y cierra el caso.
    """
    print("--- RCA REPORTER: Generando Dictamen Final y Evaluando Riesgo ---")
    
    # Obtención de contexto global
    ticket_desc = _get_attr(state, "description", "")
    failure_mode = _get_attr(state, "failure_mode", "UNKNOWN")
    timeline = _get_attr(state, "timeline", [])
    
    rag_context = rag_instance.search_playbook(ticket_desc, n_results=1)
    
    # Prompt: "Juez Final"
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Eres el RCA Reporter, el Juez Final de SARIP.\n"
                   "El equipo forense ha determinado que el fallo fue: '{failure_mode}'.\n"
                   "Tu trabajo es revisar las 'Acciones Recomendadas' en el Playbook para ese fallo y:\n"
                   "1. Determinar la acción exacta a invocar (`recommended_action`).\n"
                   "2. Calcular matemáticamente tu Confianza (0.0 a 1.0). "
                   "Si es un caso claro de timeout con playbook claro, dale 0.95. "
                   "Si la lógica es difusa o falta data, dale 0.5 y pon requires_human_approval=True.\n"
                   "3. Escribir un resumen gerencial (executive_summary) para el supervisor humano.\n"
                   "4. Ser conservador con requires_human_approval (True si el Playbook lo decreta expresamente o si confidence < 0.9)."),
        ("human", "FALLA CLASIFICADA: {failure_mode}\n\n"
                  "TIMELINE DE EVENTOS:\n{timeline}\n\n"
                  "PLAYBOOK ACTIVO:\n{rag_knowledge}")
    ])
    
    # El reporter puede usar un modelo balanceado o avanzado según el costo permitido.
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    structured_llm = llm.with_structured_output(RcaDecision)
    
    try:
        decision = structured_llm.invoke(prompt.format_messages(
            failure_mode=failure_mode,
            timeline=json.dumps(timeline, indent=2),
            rag_knowledge=rag_context
        ))
        
        rca_action = decision.recommended_action
        score = decision.confidence_score
        needs_human = decision.requires_human_approval
        summary = decision.executive_summary
        
        print(f"  > Acción Recomendada: {rca_action}")
        print(f"  > Confianza: {score} | Humano Requerido: {needs_human}")
        
    except Exception as e:
        print(f"  > Error en LLM RCA: {e}")
        rca_action = "MANUAL_REVIEW_REQUIRED_DUE_TO_ERROR"
        score = 0.0
        needs_human = True
        summary = f"Agent Exception: {e}"

    audit_msg = f"Caso concluido: {rca_action} (Seguridad: {score:.2f}, Escalar Humano: {needs_human})"
    audit = AuditLog(agent="rca_reporter", action=audit_msg).model_dump()
    
    # Retornar actualización final del Estado
    return {
        "recommended_action": rca_action,
        "confidence_score": score,
        "requires_human_approval": needs_human,
        "investigation_complete": True,
        # Opcional: Podríamos embeber el resumen gerencial dentro del state timeline o description en futuras ops.
        "next_agent": "end",
        "audit_trail": _get_attr(state, "audit_trail", []) + [audit]
    }
