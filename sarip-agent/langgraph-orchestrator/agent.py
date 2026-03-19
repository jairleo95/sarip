from typing import Dict, Any, List
from state import TicketState, AuditLog
from rag import rag_instance
import json
import os
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

import yaml

# Cargar variables de entorno (API Keys)
load_dotenv()

USE_OLLAMA = os.getenv("USE_OLLAMA", "false").lower() == "true"
LLM_CONFIG_FILE = os.getenv("SARIP_LLM_CONFIG", "config.default.yaml")

# Cargar configuración YAML
config_path = os.path.join(os.path.dirname(__file__), LLM_CONFIG_FILE)
llm_config = {}
try:
    with open(config_path, "r") as f:
        llm_config = yaml.safe_load(f).get("agents", {})
except Exception as e:
    print(f"[Warning] No se pudo cargar {LLM_CONFIG_FILE}: {e}")

def get_llm(agent_name: str = "default", temperature=0.0):
    """Devuelve el cliente LLM configurado según el agente."""
    agent_settings = llm_config.get(agent_name, {})
    temp = agent_settings.get("temperature", temperature)
    
    if USE_OLLAMA:
        model_name = agent_settings.get("model", "llama3.1")
        print(f"[LLM Config] Usando motor local para {agent_name}: Ollama ({model_name})")
        return ChatOllama(model=model_name, temperature=temp)
    else:
        model_name = agent_settings.get("model", "gpt-4o-mini")
        print(f"[LLM Config] Usando motor Cloud para {agent_name}: OpenAI ({model_name})")
        return ChatOpenAI(model=model_name, temperature=temp)

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

class ReviewerDecision(BaseModel):
    is_valid: bool = Field(description="True si la clasificación del caso está justificada por la evidencia. False si hay alucinaciones o falta lógica.")
    feedback: str = Field(description="Si is_valid es False, escribe una dura crítica al Clasificador explicando qué hizo mal y qué debe revisar. Si es True, pon 'OK'.")

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
    
    # 2. Configurar LLM Ágil
    llm = get_llm("router")
    structured_llm = llm.with_structured_output(RouterDecision)
    
    # 3. Construir el Prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Eres el Router Inicial de SARIP, un sistema de prevención y resolución de incidentes financieros.\n"
                   "Tu misión es analizar la queja del cliente y extraer información clave basándote en el extracto del Playbook.\n\n"
                   "REGLAS DE EXTRACCIÓN:\n"
                   "1. Extrae estrictamente SOLO los IDs de transacciones financieras (generalmente con prefijos como OP-, TRX-, o números de recibo).\n"
                   "2. IGNORA números de tarjetas de crédito, DNIs, teléfonos o montos.\n"
                   "3. Identifica la empresa o proveedor de servicios aludido en el ticket (ej. Claro, Movistar, AguaCorp). Si no se menciona, retorna 'UNKNOWN'.\n\n"
                   "EJEMPLOS:\n"
                   "- Ticket: 'Pagué a Movistar el recibo OP-9912 pero sigue saliendo deuda.' -> Ops: ['OP-9912'], Empresa: 'Movistar'\n"
                   "- Ticket: 'Mi tarjeta 4444... cobró de más en Sedapal.' -> Ops: [], Empresa: 'Sedapal'"),
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
    
    # 1. Agente LLM decide dinámicamente qué tools necesita
    llm = get_llm("evidence_collector")
    structured_llm = llm.with_structured_output(EvidenceDecision)
    
    for op in ops:
        print(f"  > Evaluando herramientas para {op}...")
        try:
            prompt = (f"Eres el Agente Investigador (Evidence Collector). "
                      f"Tu objetivo es decidir qué herramientas usar para investigar la transacción: {op}.\n"
                      "REGLAS:\n"
                      "1. Si es un problema de pago o estado de deuda, SIEMPRE necesitas consultar la Base de Datos (`needs_db_query` = True).\n"
                      "2. Si el cliente menciona errores, caídas, o 'no cargó la página', requieres consultar Logs (`needs_logs_query` = True).\n"
                      "Justifica tu decisión brevemente.")
            decision = structured_llm.invoke(prompt)
            print(f"  > Decisión LLM Collector: DB={decision.needs_db_query}, Logs={decision.needs_logs_query}")
            
            # 2. Invocación Real-Life al MCP Server Proxy
            if decision.needs_db_query:
                db_data = SimpleMCPClient.call_tool("get_transaction_lifecycle", {"transaction_id": op})
                db_context_gathered[op] = db_data
                
            if decision.needs_logs_query:
                trace_data = SimpleMCPClient.call_tool("query_application_logs", {"trace_id": op, "time_window_start": "now-1h", "time_window_end": "now"})
                trace_context_gathered.append(trace_data)
                
        except Exception as e:
            print(f"  > Error en LLM Collector para {op}: {e}")
    
    # 3. Empaquetar y Auditar
    audit_events = []
    
    # Agregar detalle técnico de DB al Trail
    if db_context_gathered:
        audit_events.append(AuditLog(
            agent="evidence_collector", 
            action=f"Base de Datos (Transaccional) recuperada:\n{json.dumps(db_context_gathered, indent=2)}"
        ).model_dump())
        
    # Agregar detalle técnico de Logs al Trail
    if trace_context_gathered:
        audit_events.append(AuditLog(
            agent="evidence_collector", 
            action=f"Logs de Sistema (Splunk/ELK) recuperados:\n{json.dumps(trace_context_gathered, indent=2)}"
        ).model_dump())
        
    audit_msg = f"Evidencia recopilada para {len(ops)} operaciones."
    audit_events.append(AuditLog(agent="evidence_collector", action=audit_msg).model_dump())
    
    return {
        "db_context": db_context_gathered,
        "trace_context": trace_context_gathered,
        "next_agent": "clasificador",
        "audit_trail": _get_attr(state, "audit_trail", []) + audit_events # Preservando historial
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
    search_query = f"{ticket_desc} {db_str} {trace_str}"
    rag_context = rag_instance.search_playbook(search_query, n_results=2)
    
    # Construir contexto de feedback si existe
    feedback_ctx = _get_attr(state, "reviewer_feedback")
    revision_count = _get_attr(state, "revision_count", 0)
    
    if feedback_ctx and revision_count > 0:
        system_msg = ("Eres el Clasificador Cognitivo Forense L3 del Banco.\n"
                      "¡ATENCIÓN! Tu dictamen anterior fue RECHAZADO por el Auditor Senior.\n"
                      f"FEEDBACK DEL AUDITOR: '{feedback_ctx}'.\n"
                      "Tu tarea es re-diagnosticar la falla, corrigiendo tu error lógico y basándote ESTRICTAMENTE en los Playbooks y la evidencia real.\n")
    else:
        system_msg = ("Eres el Clasificador Cognitivo Forense L3 del Banco.\n"
                      "Tu tarea es diagnosticar la causa raíz de un incidente cruzando la evidencia técnica con los 'Failure Modes' oficiales del Playbook.\n\n"
                      "PASOS:\n"
                      "1. Lee detenidamente el Playbook y sus Failure Modes.\n"
                      "2. Analiza el cruce entre los DB Records (estado transaccional) y los Logs (excepciones de sistema).\n"
                      "3. Construye un timeline cronológico mental.\n"
                      "4. Determina categóricamente el `failure_mode` EXACTO que hace match con el playbook. No inventes modos de fallo.")

    # 3. Prompt Engineering Avanzado (Cognición Forense)
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_msg),
        ("human", "<ticket>\n{ticket}\n</ticket>\n\n"
                  "<database_records>\n{db_data}\n</database_records>\n\n"
                  "<system_logs>\n{trace_data}\n</system_logs>\n\n"
                  "<official_playbook>\n{rag_knowledge}\n</official_playbook>")
    ])
    
    # Usamos el mismo motor dictado por YAML
    llm = get_llm("clasificador")
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
        "next_agent": "reviewer",
        "audit_trail": _get_attr(state, "audit_trail", []) + [audit],
        "db_context": db_ctx,
        "trace_context": trace_ctx
    }

def reviewer_agent(state: TicketState) -> dict:
    """"
    Nodo 3.5: Agente Evaluador (Critique Node)
    Supervisa y evalúa si el dictamen del Clasificador tiene sentido con la evidencia técnica.
    """
    print("--- EVALUADOR: Auditando la Calidad de la Clasificación ---")
    ticket_desc = _get_attr(state, "description", "")
    db_ctx = _get_attr(state, "db_context", {})
    trace_ctx = _get_attr(state, "trace_context", [])
    failure_mode = _get_attr(state, "failure_mode")
    timeline = _get_attr(state, "timeline", [])
    rev_count = _get_attr(state, "revision_count", 0)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Eres un Auditor Forense Senior estricto de SARIP.\n"
                   "Tu tarea es evaluar la clasificación realizada por un agente Junior. Debes verificar si el `failure_mode` "
                   "encontrado por el Junior realmente tiene un respaldo directo en la evidencia técnica (DB o Logs).\n"
                   "REGLAS:\n"
                   "1. Si el Junior alucinó un error que no está en los Logs, RECHÁZALO.\n"
                   "2. Si el Junior se inventó un `failure_mode` o hizo asunciones sin pruebas de base de datos, RECHÁZALO.\n"
                   "3. Si todo parece correcto, APRUÉBALO dictando is_valid=True.\n"
                   "4. Sé muy detallista. Es tu responsabilidad no dejar pasar Falsos Positivos."),
        ("human", "TICKET ORIGINAL: {ticket}\n\n"
                  "EVIDENCIA EN BD:\n{db}\n\n"
                  "EVIDENCIA EN LOGS:\n{logs}\n\n"
                  "CONCLUSIÓN DEL JUNIOR:\nFalla Detectada: {failure}\nTimeline:\n{timeline}")
    ])
    
    llm = get_llm("reviewer") # Reuse same config or fallback to default
    structured_llm = llm.with_structured_output(ReviewerDecision)
    
    try:
        decision = structured_llm.invoke(prompt.format_messages(
            ticket=ticket_desc,
            db=json.dumps(db_ctx, indent=2),
            logs=json.dumps(trace_ctx, indent=2),
            failure=failure_mode,
            timeline=json.dumps(timeline, indent=2)
        ))
        
        is_valid = decision.is_valid
        feedback = decision.feedback
        print(f"  > Dictamen de Auditoría: {'APROBADO' if is_valid else 'RECHAZADO'}")
        if not is_valid:
            print(f"  > Feedback al Junior: {feedback}")
            
    except Exception as e:
        print(f"  > Error en LLM Evaluador: {e}")
        is_valid = True  # Failsafe para no trabar el loop
        feedback = "Evaluador LLM Exception"
        
    action_msg = "Clasificación Validada por el Revisor." if is_valid else f"Clasificación Rechazada: {feedback}"
    audit = AuditLog(agent="reviewer", action=action_msg).model_dump()
    
    return {
        "reviewer_feedback": feedback,
        "revision_count": rev_count + 1,
        "is_valid": is_valid,
        "next_agent": "rca_reporter" if (is_valid or rev_count >= 2) else "clasificador",
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
    
    search_query = f"{ticket_desc} {failure_mode} {' '.join(timeline)}"
    rag_context = rag_instance.search_playbook(search_query, n_results=2)
    
    # Prompt: "Juez Final"
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Eres el RCA Reporter, el Juez Final de SARIP.\n"
                   "El equipo forense ha determinado que el fallo fue: '{failure_mode}'.\n"
                   "Tu trabajo es revisar las 'Acciones Recomendadas' en el Playbook para ese fallo y:\n"
                   "1. Determinar la acción exacta a invocar (`recommended_action`).\n"
                   "2. Calcular matemáticamente tu Confianza (0.0 a 1.0) usando esta rúbrica:\n"
                   "   - 0.95 a 1.0: Evidencia en DB y Logs coincide perfectamente con el Playbook.\n"
                   "   - 0.70 a 0.94: Falla identificada, pero los logs son parciales o el cliente omitió datos.\n"
                   "   - < 0.70: Evidencia contradictoria, múltiples fallos, o caso no documentado. (Setea requires_human_approval=True).\n"
                   "3. Escribir un resumen gerencial (executive_summary) para el supervisor humano.\n"
                   "4. Ser conservador con requires_human_approval (True si el Playbook lo decreta expresamente o si confidence < 0.9)."),
        ("human", "FALLA CLASIFICADA: {failure_mode}\n\n"
                  "TIMELINE DE EVENTOS:\n{timeline}\n\n"
                  "PLAYBOOK ACTIVO:\n{rag_knowledge}")
    ])
    
    # Evaluamos veredicto
    llm = get_llm("rca_reporter")
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
        "audit_trail": _get_attr(state, "audit_trail", []) + [audit],
        "db_context": _get_attr(state, "db_context", {}),
        "trace_context": _get_attr(state, "trace_context", [])
    }
