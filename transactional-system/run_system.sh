#!/bin/bash

# Service Payment System: Unified Startup and Simulation Script
# This script builds the project, starts all services via Docker Compose,
# waits for health checks, and initiates a 1-hour traffic simulation.

set -e

echo "--- Starting Service Payment System Setup ---"

# 1. Build host-side artifacts
echo "Step 1: Building project artifacts..."
./mvnw clean package -DskipTests

# 2. Start all services
echo "Step 2: Launching all services via Docker Compose..."
docker compose up -d --build --force-recreate

# 3. Wait for microservices to be healthy
echo "Step 3: Waiting for services to become healthy..."

wait_for_service() {
    local url=$1
    local name=$2
    echo "Waiting for $name at $url..."
    until curl -s "$url" > /dev/null; do
        printf "."
        sleep 2
    done
    echo -e "\n$name is UP!"
}

# Check health endpoints
wait_for_service "http://localhost:8080/q/health" "Payment Orchestrator"
wait_for_service "http://localhost:8083/q/health" "Audit Service"
wait_for_service "http://localhost:8084/q/health" "Provider Simulator"

echo "--- System is Healthy and Ready ---"

echo "Step 3.5: Seeding test accounts into the database..."
docker cp seed_accounts.sql payment_db:/tmp/
docker exec -i payment_db psql -U user -d payment_db -f /tmp/seed_accounts.sql

# 4. Trigger traffic simulation
echo "Step 4: Launching traffic simulation (300 TPS) for ${1:-1} hours..."
python3 performance_simulation.py ${1:-1}

echo "--- Simulation Complete ---"
