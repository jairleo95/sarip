import asyncio
import aiohttp
import time
import uuid
import statistics
import sys
import random

# Configuration
URL = "http://localhost:8080/api/v1/payments"
ACCOUNTS = [f"ACC-{i}" for i in range(1, 101)]
SERVICE_ID = "STRESS"
TARGET_TPS = 300
DURATION_SECONDS = 60

if len(sys.argv) > 1:
    try:
        DURATION_SECONDS = int(sys.argv[1])
    except ValueError:
        pass

TOTAL_REQUESTS = TARGET_TPS * DURATION_SECONDS

async def send_payment(session, stats):
    start_time = time.perf_counter()
    idempotency_key = str(uuid.uuid4())
    account_id = random.choice(ACCOUNTS)
    payload = {
        "service_id": SERVICE_ID,
        "customer_reference": f"STRESS-{int(time.time()*1000)}",
        "amount": round(random.uniform(1.0, 100.0), 2),
        "currency": "USD",
        "account_id": account_id
    }
    
    try:
        async with session.post(URL, json=payload, headers={"X-Idempotency-Key": idempotency_key}, timeout=10) as response:
            latency = time.perf_counter() - start_time
            stats['latencies'].append(latency)
            if response.status == 201:
                stats['success'] += 1
            else:
                stats['failures'] += 1
                stats['error_codes'][response.status] = stats['error_codes'].get(response.status, 0) + 1
    except Exception as e:
        stats['failures'] += 1
        stats['exceptions'] += 1

async def main():
    print(f"Starting Stress Test: {TARGET_TPS} TPS for {DURATION_SECONDS}s...")
    print(f"Target Total: {TOTAL_REQUESTS} requests.")
    
    stats = {
        'success': 0,
        'failures': 0,
        'exceptions': 0,
        'latencies': [],
        'error_codes': {}
    }
    
    # Limit maximum concurrent in-flight requests to avoid client-side resource exhaustion
    semaphore = asyncio.Semaphore(100) 

    async def sem_send_payment(session, stats):
        async with semaphore:
            await send_payment(session, stats)

    async with aiohttp.ClientSession() as session:
        start_time = time.perf_counter()
        tasks = []
        
        for i in range(TOTAL_REQUESTS):
            tasks.append(asyncio.create_task(sem_send_payment(session, stats)))
            
            # Rate limiting logic
            elapsed = time.perf_counter() - start_time
            expected_total = i + 1
            actual_tps = expected_total / (elapsed + 0.0001)
            
            if actual_tps > TARGET_TPS:
                await asyncio.sleep(max(0, (expected_total / TARGET_TPS) - elapsed))
                
            if i % 1000 == 0 and i > 0:
                print(f"Progress: {i}/{TOTAL_REQUESTS} requests sent...")
        
        await asyncio.gather(*tasks)
        
    total_time = time.perf_counter() - start_time
    print("\n--- Stress Test Results ---")
    print(f"Total Time: {total_time:.2f}s")
    print(f"Total Requests: {stats['success'] + stats['failures']}")
    print(f"Successful: {stats['success']}")
    print(f"Failures: {stats['failures']} (Exceptions: {stats['exceptions']})")
    if stats['error_codes']:
        print(f"Error Distribution: {stats['error_codes']}")
    
    if stats['latencies']:
        p50 = statistics.median(stats['latencies']) * 1000
        p95 = statistics.quantiles(stats['latencies'], n=20)[18] * 1000
        p99 = statistics.quantiles(stats['latencies'], n=100)[98] * 1000
        print(f"Latency P50: {p50:.2f}ms")
        print(f"Latency P95: {p95:.2f}ms")
        print(f"Latency P99: {p99:.2f}ms")
    
    actual_throughput = stats['success'] / total_time
    print(f"Actual Throughput: {actual_throughput:.2f} TPS")
    print(f"Equivalent Hourly Rate: {actual_throughput * 3600:,.0f} ops/hour")

if __name__ == "__main__":
    asyncio.run(main())
