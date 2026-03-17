import psycopg2
import sys
import time
from main import start_sarip_investigation

def fetch_failed_transactions(limit=3):
    """Obtiene las transacciones fallidas más recientes directamente de la base de datos."""
    print("Conectando a PostgreSQL (payment_db) para buscar casos reales...")
    try:
        conn = psycopg2.connect(
            dbname="payment_db",
            user="user",
            password="password",
            host="localhost",
            port="5432"
        )
        cur = conn.cursor()
        
        # Buscar las últimas fallidas
        query = """
            SELECT id, service_id, customer_reference, amount 
            FROM transactions 
            WHERE status = 'FAILED' 
            ORDER BY created_at DESC 
            LIMIT %s
        """
        cur.execute(query, (limit,))
        rows = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return rows
        
    except psycopg2.errors.UndefinedTable:
        print("\n[!] ERROR: La tabla 'transactions' no existe.")
        print("    Asegúrate de ejecutar ./run_system.sh dentro de /transactional-system primero.")
        sys.exit(1)
    except Exception as e:
        print(f"\n[!] ERROR al conectar a DB: {e}")
        print("    Asegúrate de que el contenedor de PostgreSQL esté corriendo (docker ps).")
        sys.exit(1)

import httpx

def run_live_investigations():
    transactions = fetch_failed_transactions(3)
    
    if not transactions:
        print("\nNo se encontraron transacciones en estado FAILED.")
        print("Ejecuta ./run_system.sh para simular tráfico y generar errores.")
        return
        
    print(f"\nSe encontraron {len(transactions)} transacciones fallidas. Enviando al Ticketing...\n")
    
    # Ticketing API URL
    TICKETING_BASE_URL = "http://localhost:9999/api/cases"
    
    for i, row in enumerate(transactions, 1):
        trx_id = str(row[0])
        service = row[1]
        ref = row[2]
        amount = row[3]
        
        # Generar un ticket sintético
        ticket_title = f"Reclamo por cobro fallido {service} (Ref: {ref})"
        ticket_text = f"Hola banco, intenté pagar mi recibo {ref} de la empresa {service} por un monto de {amount} USD. En mi app salió error pero no sé si se procesó. La operación es la {trx_id}. Mi DNI es 74125896, por favor ayuda."
        
        print("=" * 60)
        print(f" CASO REAL #{i} | TX: {trx_id}")
        print("=" * 60)
        
        # 1. Crear el Ticket en el Frontend
        print(">> 1. Reportando caso al Frontend de Ticketing...")
        try:
            create_res = httpx.post(TICKETING_BASE_URL, json={
                "title": ticket_title,
                "description": ticket_text,
                "severity": "high"
            }, timeout=5.0)
            
            if create_res.status_code != 201:
                print(f"[!] Error creando ticket en Next.js: {create_res.text}")
                continue
                
            case_data = create_res.json()
            case_id = case_data.get("id")
            print(f"✅ Ticket creado exitosamente con ID: {case_id}")
            
            # 2. Iniciar Investigación SARIP (End-to-End via API)
            print(">> 2. Iniciando investigación SARIP a través del sistema...")
            start_time = time.time()
            
            analyze_url = f"{TICKETING_BASE_URL}/{case_id}/analyze"
            analyze_res = httpx.post(analyze_url, timeout=60.0) # LangGraph puede demorar
            
            elapsed = time.time() - start_time
            
            if analyze_res.status_code == 200:
                final_state = analyze_res.json()
                analysis = final_state.get("analysis", {})
                print(f"\n🎯 DICTAMEN FINAL SARIP (en {elapsed:.2f}s):")
                print(f"  * Fallo Detectado: {analysis.get('failureMode')}")
                print(f"  * Acción (RCA):    {analysis.get('recommendedAction')} (Score: {analysis.get('confidenceScore')})")
                print(f"  * Escalar humano:  {analysis.get('requiresHumanApproval')}")
                print(f"🔗 Puedes verlo en la UI: http://localhost:9999/cases/{case_id}")
            else:
                print(f"[!] Error ejecutando análisis SARIP: {analyze_res.text}")
                
            print("-" * 60)
            
        except httpx.ConnectError:
            print("[!] Error: No se pudo conectar al servidor de Ticketing (http://localhost:9999).")
            print("¿Está corriendo Next.js en la otra terminal?")
            break
        except Exception as e:
            print(f"[!] Error general: {e}")

if __name__ == "__main__":
    run_live_investigations()
