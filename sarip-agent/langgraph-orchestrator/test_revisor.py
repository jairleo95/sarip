import asyncio
from state import TicketState
import agent
import json

def test_forced_rejection():
    print("==================================================")
    print("🔥 INICIANDO PRUEBA DE ESTRES: FORZANDO ALUCINACIÓN")
    print("==================================================")
    
    # Creamos un Estado Falso donde el "Clasificador Junior" cometió un error grave
    # (Diciendo que hubo un Timeout Crítico cuando la base de datos dice COMPLETED y no hay excepciones)
    estado_falso = TicketState(
        ticket_id="TEST-HALLUCINATION",
        description="El cliente dice que la app se congeló al pagar la luz.",
        operations=["OPE-999"],
        db_context={"OPE-999": {"status": "COMPLETED", "amount": 100}},
        trace_context=[{"logs_found": 0, "exceptions": [], "message": "No errors."}],
        failure_mode="CRITICAL_DATABASE_CORRUPTION_TIMEOUT", # ¡Una mentira enorme!
        timeline=["00:00 - Cliente paga", "00:01 - BD Explota"]
    )
    
    print("\n[INPUT AL REVISOR]")
    print(f"Falla acusada por Junior: {estado_falso.failure_mode}")
    print(f"Evidencia real (DB): {estado_falso.db_context}")
    print(f"Evidencia real (Logs): {estado_falso.trace_context}\n")
    
    # Invocamos directamente al Nodo Revisor
    resultado = agent.reviewer_agent(estado_falso)
    
    print("\n[OUTPUT DEL REVISOR]")
    print(json.dumps(resultado, indent=2))
    
if __name__ == "__main__":
    test_forced_rejection()
