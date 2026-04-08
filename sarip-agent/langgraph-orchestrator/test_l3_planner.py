import sys
import os

# Ensure we can import planner_agent
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from planner_agent import deep_research_ticket

ticket_context = """
# TICKET-504: Timeout Masivo en Producción
Descripción del Usuario: "La página se congela y arroja HTTP 504 Gateway Timeout cuando intento realizar pagos de servicio de internet a proveedor Claro."
Logs superficiales encontrados: No hay excepciones NullPointer ni StackTraces, solo caídas abruptas de conexión HTTP.

El nivel 1 y 2 no saben qué pasó. Parece un fallo de saturación de infraestructura.
Usa tu tool de `query_prometheus_metrics` pasándole una consulta PromQL real (ej. up, process_cpu_seconds_total, u otras métricas básicas) para averiguar si el microservicio orquestador u otro contenedor falló o está saturado de CPU/RAM.
Diagnostica la causa raíz y escribe el L3 Forensic Report.
"""

if __name__ == "__main__":
    print("🚀 Lanzando Test Automático de Nivel 3 (L3 Planner con PROMETHEUS)...")
    print("Simulando un apagón de APM.\n")
    
    try:
        resultado = deep_research_ticket(ticket_context)
        print("\n" + "="*60)
        print("🎯 L3 FORENSIC REPORT RECIBIDO:")
        print("="*60)
        print(resultado)
        
        with open("l3_apm_test_result.txt", "w", encoding="utf-8") as f:
            f.write(resultado)
    except Exception as e:
        print(f"Error drástico en el test: {e}")
