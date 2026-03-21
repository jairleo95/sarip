import httpx
import uuid
import psycopg2
from main import start_sarip_investigation
from langchain_ollama import ChatOllama
import json
import time

def get_real_errors_from_kibana(limit=3):
    """
    Busca los últimos logs de ERROR en Elasticsearch que tengan un trace_id.
    """
    print("1. Consultando ElasticSearch (Kibana) por errores recientes...")
    query = {
        "size": limit * 3, # Traemos mas para filtrar repetidos
        "query": {
            "bool": {
                "must": [
                    {"match": {"level_name": "ERROR"}},
                    {"exists": {"field": "trace_id"}}
                ]
            }
        },
        "sort": [{"@timestamp": {"order": "desc"}}]
    }
    
    try:
        res = httpx.post(
            "http://localhost:9200/service-payment-logs-*/_search",
            json=query,
            timeout=10.0
        )
        if res.status_code != 200:
            print(f"[!] Error de Elasticsearch: {res.status_code} - {res.text}")
            return []
            
        hits = res.json().get("hits", {}).get("hits", [])
        
        extracted_errors = {}
        for hit in hits:
            source = hit["_source"]
            trace_id = source.get("trace_id")
            
            # Filtramos trace_id ya procesados
            if trace_id and trace_id not in extracted_errors:
                extracted_errors[trace_id] = {
                    "trace_id": trace_id,
                    "message": source.get("message", "Error"),
                    "stack_trace": source.get("StackTrace", ""),
                    "timestamp": source.get("@timestamp")
                }
                if len(extracted_errors) >= limit:
                    break
                    
        return list(extracted_errors.values())
        
    except httpx.RequestError as e:
        print(f"[!] No se pudo conectar a Elasticsearch: {e}")
        return []

def get_transaction_details(trace_id):
    """
    Obtiene los detalles del ticket transaccional (monto, servicio, cuenta) de PostgreSQL.
    """
    try:
        conn = psycopg2.connect(
            dbname="payment_db", 
            user="user", 
            password="password", 
            host="localhost", 
            port="5432"
        )
        cur = conn.cursor()
        cur.execute("SELECT amount, currency, service_id, account_id FROM transactions WHERE id = %s", (trace_id,))
        row = cur.fetchone()
        conn.close()
        
        if row:
            return {
                "amount": float(row[0]),
                "currency": row[1],
                "service_id": row[2],
                "account_id": row[3]
            }
    except Exception as e:
        print(f"[!] No se pudo consultar Postgres para {trace_id}: {e}")
        
    return None

def synthesize_user_ticket(error_log, tx_details):
    """
    Utiliza el LLM local para traducir un Log Técnico (Backend) en un Ticket de Usuario organico.
    """
    llm = ChatOllama(model="llama3.1", temperature=0.7)
    
    print(f"2. Sintetizando queja de usuario para trace {error_log['trace_id']} usando Llama 3.1...")
    
    amount_str = f"{tx_details['amount']} {tx_details['currency']}" if tx_details else "un monto desconocido"
    service_str = tx_details['service_id'] if tx_details else "un servicio"
    account_str = tx_details['account_id'] if tx_details else "mi cuenta"
    
    prompt = f"""
    Eres un usuario muy molesto de un banco que acaba de experimentar un error al intentar pagar su servicio.
    Aquí están los detalles técnicos internos (que tú como usuario NO sabes pero que te pasaron factura):
    - Error del sistema: {error_log['message']}
    - Servicio que intentabas pagar: {service_str}
    - Monto involucrado: {amount_str}
    - ID de Operacion que te tiro el app: {error_log['trace_id']}
    
    INSTRUCCIONES:
    - Redacta de forma muy natural y en primera persona tu reporte de incidente al banco.
    - Máximo 3 oraciones cortas.
    - DEBES INCLUIR tu ID de Operacion ({error_log['trace_id']}), la empresa a la que pagaste ({service_str}) y el monto que intentaste pagar.
    - NO menciones código Java ni excepciones, actúa como una persona frustrada usando la banca movil.
    """
    
    response = llm.invoke(prompt)
    return response.content.strip()

def main():
    print("=================================================================")
    print("🤖 SARIP: REAL DATA EXTRACTION & RESOLUTION PIPELINE INIT")
    print("=================================================================\n")
    
    # 1. Extraer los últimos N errores de la vida real de Kibana
    real_errors = get_real_errors_from_kibana(limit=2)
    
    if not real_errors:
        print("No se encontraron errores recientes en Kibana. Intenta encender el trafic simulator (performance_simulation.py).")
        return
        
    print(f"✅ Se encontraron {len(real_errors)} errores únicos en los logs de producción.\n")
    
    for idx, error in enumerate(real_errors):
        trace_id = error["trace_id"]
        print(f"\n[{idx + 1}] PROCESANDO INCIDENTE PARA TRACE_ID: {trace_id}")
        print("-" * 60)
        
        # 2. Correlación con Base de Datos Transaccional (Para saber el monto etc)
        tx_details = get_transaction_details(trace_id)
        
        # 3. Sintetizar un Ticket usando Llama
        user_complaint = synthesize_user_ticket(error, tx_details)
        print("\n📝 [TICKET SINTETIZADO]:")
        print(f"DESCRIPCION: {user_complaint}\n")
        
        print("3. Inyectando el ticket al Dashboard de Ticketing (Next.js)...")
        try:
            # POST the ticket to the Next.js API
            ticket_payload = {
                "title": f"Fallo Crítico reportado en App Móvil (Operación: {trace_id[-6:]})",
                "description": user_complaint,
                "severity": "high"
            }
            res_create = httpx.post("http://localhost:9999/api/cases", json=ticket_payload)
            if res_create.status_code == 200:
                ticket_data = res_create.json()
                ticket_id = ticket_data.get("id")
                print(f"✅ Ticket creado exitosamente en la UI con ID: {ticket_id}")
                
                print("4. Solicitando a la UI que dispare el Análisis IA (LangGraph)...")
                # Trigger the analyze endpoint on Next.js
                time.sleep(1) # Pequeña pausa
                start_time = time.time()
                res_analyze = httpx.post(f"http://localhost:9999/api/cases/{ticket_id}/analyze", timeout=120.0)
                elapsed = time.time() - start_time
                
                if res_analyze.status_code == 200:
                    analysis_result = res_analyze.json()
                    print(f"\n🏆 [IA DIAGNOSTICO] (Duración: {elapsed:.2f}s)")
                    print(f"  Fallo Identificado: {analysis_result.get('failureMode')}")
                    print(f"  Acción Recomendada: {analysis_result.get('recommendedAction')} (Score: {analysis_result.get('confidenceScore')})")
                    print(f"  Aprobación Humana: {analysis_result.get('requiresHumanApproval')}")
                    
                    print(f"\n👉 ¡Ve al portal http://localhost:9999 y busca el ticket {ticket_id} para verlo!")
                else:
                    print(f"[!] Error al analizar en la UI: {res_analyze.status_code}")
            else:
                print(f"[!] Error al crear ticket en la UI: {res_create.status_code}")
        except Exception as e:
            print(f"[!] Excepción de red contactando Next.js: {e}")
            
    print("\n=================================================================")
    print("✅ CICLO FORENSE DE DATA REAL FINALIZADO")
    print("=================================================================")

if __name__ == "__main__":
    main()
