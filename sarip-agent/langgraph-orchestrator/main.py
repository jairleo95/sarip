from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from state import TicketState
import agent
from pii_masker import mask_pii
import json

# 1. Definir el Grafo Base de LangGraph apuntando a nuestro Pydantic BaseModel
workflow = StateGraph(TicketState)

# 2. Añadir los Nodos (Agentes Lógicos de agent.py)
workflow.add_node("router", agent.router_agent)
workflow.add_node("evidence_collector", agent.evidence_collector)
workflow.add_node("clasificador", agent.clasificador)
workflow.add_node("reviewer_agent", agent.reviewer_agent)
workflow.add_node("rca_reporter", agent.rca_reporter)
workflow.add_node("human_approval", agent.human_approval)

# 3. Definir el flujo Asíncrono Funcional (Edges)
# Nodo Inicial (Triage)
workflow.set_entry_point("router")

# Definimos el flujo determinista (Pipeline Causal)
# (En un futuro v2 de SARIP se podrían usar Conditional Edges dinámicos, pero 
# el flujo ideal forense es lineal: Evaluar -> Extraer -> Pensar -> Escribir).
workflow.add_edge("router", "evidence_collector")
workflow.add_edge("evidence_collector", "clasificador")
workflow.add_edge("clasificador", "reviewer_agent")

def check_review_status(state: TicketState) -> str:
    # Si fue aprobado, o si ya alcanzó el límite de reintentos
    if getattr(state, "is_valid", False) or getattr(state, "revision_count", 0) >= 2:
        return "rca_reporter"
    return "clasificador"

workflow.add_conditional_edges(
    "reviewer_agent",
    check_review_status,
    {
        "rca_reporter": "rca_reporter",
        "clasificador": "clasificador"
    }
)

def check_human_approval(state: TicketState) -> str:
    # Función que rutea a Aprobación Humana si el LLM lo ordenó en RCA
    if getattr(state, "requires_human_approval", False):
        return "human_approval"
    return END

# Reemplazamos el edge directo por uno condicional desde rca_reporter
workflow.add_conditional_edges(
    "rca_reporter",
    check_human_approval,
    {
        "human_approval": "human_approval",
        END: END
    }
)

# Punto de Salida definitivo tras intervención humana
workflow.add_edge("human_approval", END)

# 4. Compilar el Grafo con Checkpointer (Memoria para Pausas)
memory = MemorySaver()
sarip_app = workflow.compile(
    checkpointer=memory, 
    interrupt_before=["human_approval"] # Langgraph se congela antes de entrar aquí
)

def start_sarip_investigation(raw_ticket_text: str, ticket_id: str):
    """
    Función de entrada del sistema principal.
    Aplica PII Masking antes de iniciar el estado.
    """
    print("="*60)
    print(f"🚀 INICIANDO SARIP LangGraph Execution | TICKET: {ticket_id}")
    print("="*60)
    
    # Capa de Seguridad Inbound 0: Enmascarar Datos Privados (PII)
    safe_description = mask_pii(raw_ticket_text)
    print(f"[🛡️ PII Masker] Texto original ofuscado. Previniendo fuga de datos.\n")
    
    # Crear el JSON 'Case File' Inicial de Estado
    initial_state = {
        "ticket_id": ticket_id,
        "description": safe_description,
    }
    
    # Configurar el Thread ID para que el Checkpointer sepa qúe sesión "pausar/reanudar"
    config = {"configurable": {"thread_id": ticket_id}}
    
    # Ejecutar el grafo. stream() nos permite ver cada nodo conforme termina (Observability)
    for output in sarip_app.stream(initial_state, config=config):
        for node_name, state in output.items():
            print(f"✅ Nodo finalizado: {node_name}")
            print("-" * 40)
            
    # Verificar si el pipeline está "interrumpido" esperando humano
    graph_state = sarip_app.get_state(config)
    if graph_state.next and "human_approval" in graph_state.next:
        print(f"\n⏸️  [HITL PAUSE] La IA (rca_reporter) dictaminó confidence bajo o riesgo alto.")
        print(f"⏸️  El Grafo se ha congelado automáticamente en Thread ID: {ticket_id}")
        print("⏸️  Esperando click de RESUME en el UI (Post /resume_investigation) ...")
        
        
    # Guardar en Memoria a Largo Plazo Reflexiva
    from reflective_memory import check_and_update_memory
    if 'state' in locals():
        check_and_update_memory(
            ticket_id=ticket_id,
            failure_mode=state.get("failure_mode", ""),
            action=state.get("recommended_action", ""),
            description=safe_description
        )
        
    return state # Estado final o pausado

if __name__ == "__main__":
    
    # CASO DE PRUEBA: "Timeout de la Empresa" o "Reconciliation" (Golden Dataset)
    # Contiene datos sensibles falsos a ofuscar (correo y cuenta).
    texto_reclamo = (
        "Hola mi correo es juan_perez99@gmail.com. "
        "Ayer hice un pago a Telecom (Claro/Movistar) con mi tarjeta 4555 1111 2222 3333 "
        "por la operacion op-7489 y aun me figura que debo. "
        "Mi DNI es 72124567 por favor revisen."
    )
    
    estado_final = start_sarip_investigation(
        raw_ticket_text=texto_reclamo, 
        ticket_id="TCK-10029"
    )

    print("\n" + "="*60)
    print(f"🎯 INVESTIGACIÓN FINALIZADA. RESUMEN DEL CASE FILE GENERADO:")
    print("="*60)
    print(f"RCA Action: {estado_final.get('recommended_action')}")
    print(f"Score (0-1): {estado_final.get('confidence_score')}")
    print(f"Requiere Aprobación Humana: {estado_final.get('requires_human_approval')}")
    print("\nAuditoría Completa de la IA:")
    audit_trail_dicts = [a.model_dump() if hasattr(a, 'model_dump') else a for a in estado_final.get("audit_trail", [])]
    print(json.dumps(audit_trail_dicts, indent=2))
