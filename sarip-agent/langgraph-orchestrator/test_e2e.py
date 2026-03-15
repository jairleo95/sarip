from main import start_sarip_investigation
import json
import time

def run_golden_dataset():
    """
    Pruebas E2E: Ejecuta 3 tickets diseñados para disparar reglas distintas de los Playbooks (RAG).
    Valida el enmascaramiento PII, el ruteo de herramientas MCP, y el razonamiento LLM.
    """
    
    dataset = [
        {
            "id": "TCK-GOLD-001",
            "name": "Caso 1: Timeout AguaCorp (Business Error)",
            "ticket": "El usuario mariano.perez@empresa.com reporta que pagó su recibo de AguaCorp con DNI 09918231. "
                      "La operación figura como op-8812 pero le siguen cobrando mora. "
                      "Favor validar si la empresa recibió el dinero."
        },
        {
            "id": "TCK-GOLD-002",
            "name": "Caso 2: Inconsistencia Claro/Movistar (Reconciliation Mismatch)",
            "ticket": "Problema grave. El archivo SFTP de Movistar de hoy dice que no tienen el pago de la linea "
                      "999888777 (operación trx-49112). Sin embargo en nuestro core sí descontamos de la tarjeta "
                      "terminada en 4444-5555-****-9900. El cliente va a ir a Indecopi."
        },
        {
            "id": "TCK-GOLD-003",
            "name": "Caso 3: Problema de BD Core (Infra / Deadlock)",
            "ticket": "Soy de operaciones IT. Tuvimos un pico de uso ayer a las 10am. Varios pagos daban error interno. "
                      "Específicamente el cliente con cuenta bancaria 88-1111-2222 se queja de la transacción pmt-889. "
                      "Seguro fue un deadlock. Revisen."
        }
    ]

    print("=========================================================")
    print("🚀 INICIANDO SUITE E2E: GOLDEN DATASET TESTING PARA SARIP")
    print("=========================================================\n")

    results = []

    for test_case in dataset:
        print(f"\n>> EJECUTANDO {test_case['name']} ({test_case['id']})")
        print(f">> TICKET ORIGINAL: {test_case['ticket']}\n")
        
        start_time = time.time()
        
        try:
            # Ejecutar el Pipeline Forense LangGraph
            final_state = start_sarip_investigation(
                raw_ticket_text=test_case["ticket"], 
                ticket_id=test_case["id"]
            )
            
            elapsed = time.time() - start_time
            
            # Recolectar resultados clave para el reporte
            results.append({
                "case_id": test_case['id'],
                "name": test_case['name'],
                "failure_mode": final_state.get("failure_mode"),
                "recommended_action": final_state.get("recommended_action"),
                "confidence_score": final_state.get("confidence_score"),
                "requires_human": final_state.get("requires_human_approval"),
                "duration_seconds": round(elapsed, 2)
            })
            
            print(f"\n<< EJECUCIÓN COMPLETADA EN {elapsed:.2f}s")
            print("-" * 50)
            
        except Exception as e:
            print(f"\n[!] ERROR CRÍTICO AL EJECUTAR CASO {test_case['id']}: {e}")

    # Imprimir Reporte Final E2E
    print("\n" + "="*60)
    print("📊 REPORTE FINAL E2E - MATRIZ DE RESULTADOS")
    print("="*60)
    for res in results:
        print(f"[{res['case_id']}] {res['name']}")
        print(f"  * Fallo Detectado: {res['failure_mode']}")
        print(f"  * Veredicto RCA:   {res['recommended_action']} (Score: {res['confidence_score']})")
        print(f"  * Esperando Human: {res['requires_human']}")
        print(f"  * Tiempo Proceso:  {res['duration_seconds']}s")
        print("-" * 40)

if __name__ == "__main__":
    run_golden_dataset()
