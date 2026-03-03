import asyncio
import aiohttp
import time
import uuid
import random
import sys
import statistics
from datetime import datetime, timedelta

# Configuration
URL = "http://localhost:8080/api/v1/payments"
ACCOUNTS = [f"ACC-{i:03d}" for i in range(1, 6)]
TARGET_TPS = 300
DURATION_HOURS = 1
LOG_INTERVAL_SECONDS = 60

if len(sys.argv) > 1:
    try:
        DURATION_HOURS = float(sys.argv[1])
    except ValueError:
        pass

DURATION_SECONDS = int(DURATION_HOURS * 3600)

class Stats:
    def __init__(self):
        self.success = 0
        self.failures = 0
        self.latencies = []
        self.error_codes = {}
        self.start_time = time.perf_counter()
        self.interval_start = time.perf_counter()
        self.interval_success = 0
        self.interval_failures = 0

    def record(self, status, latency):
        if status == 201:
            self.success += 1
            self.interval_success += 1
        else:
            self.failures += 1
            self.interval_failures += 1
            self.error_codes[status] = self.error_codes.get(status, 0) + 1
        self.latencies.append(latency)
        # Keep only last 10000 latencies to save memory
        if len(self.latencies) > 10000:
            self.latencies = self.latencies[-10000:]

    def report_interval(self):
        now = time.perf_counter()
        duration = now - self.interval_start
        tps = (self.interval_success + self.interval_failures) / duration
        
        p50 = statistics.median(self.latencies[-1000:]) * 1000 if self.latencies else 0
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Pulse: {tps:.2f} TPS | Success: {self.interval_success} | Fail: {self.interval_failures} | P50: {p50:.2f}ms")
        
        self.interval_start = now
        self.interval_success = 0
        self.interval_failures = 0

async def send_payment(session, stats, semaphore):
    async with semaphore:
        idempotency_key = str(uuid.uuid4())
        account_id = random.choice(ACCOUNTS)
        companies = [
            "LuzDelSur", "Sedapal", "Movistar", "Claro", "Entel", "Bitel", 
            "Calidda", "Enel", "Interbank-Seguros", "Rimac-Eps", "Pacifico-Seguros",
            "EsSalud", "Sunat", "Sat-Arbitrios", "Univ-UNI", "Univ-SanMarcos",
            "Univ-PUCP", "Colegio-Lima", "GNV-Carga", "GLP-Hogar", "Cable-Plus",
            "Internet-Fibra", "Gimnasio-Smart", "Club-Regatas", "Inmob-Azul",
            "Condom-Verde", "Banco-Nacion", "Caja-Piura", "Caja-Huancayo", "Sodexo"
        ]
        service_id = random.choice(companies)
        payload = {
            "service_id": service_id,
            "customer_reference": f"SIM-{int(time.time()*1000)}",
            "amount": 10.0,
            "currency": "USD",
            "account_id": account_id
        }
        
        start_time = time.perf_counter()
        try:
            async with session.post(URL, json=payload, headers={"X-Idempotency-Key": idempotency_key}, timeout=5) as resp:
                latency = time.perf_counter() - start_time
                stats.record(resp.status, latency)
        except Exception as e:
            stats.record(599, 0) # Use 599 for client-side exceptions

async def main():
    print(f"--- Starting Long-Run Payment Simulation ---")
    print(f"Target: {TARGET_TPS} TPS | Duration: {DURATION_HOURS} hours")
    print(f"Metrics interval: {LOG_INTERVAL_SECONDS} seconds")
    
    stats = Stats()
    semaphore = asyncio.Semaphore(200) # Control max in-flight requests
    
    async with aiohttp.ClientSession() as session:
        end_time = time.perf_counter() + DURATION_SECONDS
        last_log = time.perf_counter()
        
        # We use a loop that controls the rate without gathering everything
        request_count = 0
        loop_start = time.perf_counter()
        
        while time.perf_counter() < end_time:
            # Dispatch a batch or single request
            asyncio.create_task(send_payment(session, stats, semaphore))
            request_count += 1
            
            # Rate limiting
            now = time.perf_counter()
            expected_time = loop_start + (request_count / TARGET_TPS)
            wait_time = expected_time - now
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            
            # Periodic reporting
            if now - last_log >= LOG_INTERVAL_SECONDS:
                stats.report_interval()
                last_log = now

    total_time = time.perf_counter() - stats.start_time
    print("\n--- Final Simulation Summary ---")
    print(f"Total Duration: {timedelta(seconds=int(total_time))}")
    print(f"Total Requests: {stats.success + stats.failures}")
    print(f"Overall Success: {stats.success} ({(stats.success/(stats.success+stats.failures))*100:.2f}%)")
    print(f"Overall Throughput: {(stats.success + stats.failures)/total_time:.2f} TPS")
    if stats.error_codes:
        print(f"Error Distribution: {stats.error_codes}")

if __name__ == "__main__":
    asyncio.run(main())
