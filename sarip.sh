#!/bin/bash

# ==============================================================================
# SARIP Ecosystem Manager Script
# ==============================================================================

# Directories
PROJECT_ROOT="/home/darkstar/Workspace/dev/service-payment"
TICKETING_DIR="$PROJECT_ROOT/sarip-ticketing"
MCP_DIR="$PROJECT_ROOT/sarip-agent/mcp-gateway"
ORCHESTRATOR_DIR="$PROJECT_ROOT/sarip-agent/langgraph-orchestrator"
TRANSACTIONAL_DIR="$PROJECT_ROOT/transactional-system"

# PID files
PID_DIR="/tmp/sarip_pids"
TICKETING_PID="$PID_DIR/ticketing.pid"
MCP_PID="$PID_DIR/mcp.pid"
ORCHESTRATOR_PID="$PID_DIR/orchestrator.pid"

mkdir -p "$PID_DIR"

print_header() {
    echo "=================================================="
    echo "             🤖 SARIP ECOSYSTEM CONTROLLER        "
    echo "=================================================="
}

start_core() {
    print_header
    echo "Levantando Sistema Transaccional (Docker Compose)..."
    cd "$TRANSACTIONAL_DIR"
    
    # Check if we need to build and run system (run_system.sh) or just docker compose
    if [ ! -d "target" ]; then
        echo "Building artifacts first..."
        ./mvnw clean package -DskipTests
    fi
    
    docker compose up -d
    echo "✅ Core Bancario iniciado en Docker."
}

run_system() {
    local duration=${1:-1}
    print_header
    echo "--- Starting Service Payment System Setup (Simulation Mode) ---"
    cd "$TRANSACTIONAL_DIR"
    
    echo "Step 1: Building project artifacts..."
    ./mvnw clean package -DskipTests
    
    echo "Step 2: Launching all services via Docker Compose..."
    docker compose up -d --build --force-recreate
    
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
    
    wait_for_service "http://localhost:8080/q/health" "Payment Orchestrator"
    wait_for_service "http://localhost:8083/q/health" "Audit Service"
    wait_for_service "http://localhost:8084/q/health" "Provider Simulator"
    wait_for_service "http://localhost:5601/api/status" "Kibana"
    
    echo "--- System is Healthy and Ready ---"
    
    echo "Step 3.1: Provisioning Kibana Default Index Pattern..."
    curl -s -X POST "http://localhost:5601/api/saved_objects/index-pattern/service-payment-logs" \
      -H 'kbn-xsrf: true' \
      -H 'Content-Type: application/json' \
      -d '{"attributes":{"title":"service-payment-logs-*","timeFieldName":"@timestamp"}}' > /dev/null
    echo -e "\nKibana Index Pattern configured."
    
    echo "Step 3.5: Seeding test accounts into the database..."
    docker cp seed_accounts.sql payment_db:/tmp/
    docker exec -i payment_db psql -U user -d payment_db -f /tmp/seed_accounts.sql
    
    echo "Step 4: Launching traffic simulation (300 TPS) for $duration hour(s)..."
    nohup python3 performance_simulation.py "$duration" > simulation.log 2>&1 &
    
    echo "✅ Simulation Triggered in background (see simulation.log)"
}

stop_core() {
    print_header
    echo "Deteniendo Sistema Transaccional..."
    cd "$TRANSACTIONAL_DIR"
    docker compose down
    echo "✅ Core Bancario detenido y redes limpiadas."
}

start_services() {
    print_header
    echo "Iniciando servicios en segundo plano..."
    
    # 1. Start MCP Gateway
    if [ -f "$MCP_PID" ] && kill -0 $(cat "$MCP_PID") 2>/dev/null; then
        echo "✅ MCP Gateway ya está corriendo (Port 8081)."
    else
        echo "🚀 Iniciando MCP Gateway (Port 8081)..."
        cd "$MCP_DIR"
        source ../langgraph-orchestrator/.venv/bin/activate
        nohup python server.py > mcp_gateway.log 2>&1 &
        echo $! > "$MCP_PID"
        deactivate
    fi

    # 2. Start LangGraph Orchestrator
    if [ -f "$ORCHESTRATOR_PID" ] && kill -0 $(cat "$ORCHESTRATOR_PID") 2>/dev/null; then
        echo "✅ LangGraph Orchestrator ya está corriendo (Port 8000)."
    else
        echo "🚀 Iniciando LangGraph Orchestrator (Port 8000)..."
        cd "$ORCHESTRATOR_DIR"
        source .venv/bin/activate
        nohup python server.py > orchestrator.log 2>&1 &
        echo $! > "$ORCHESTRATOR_PID"
        deactivate
    fi

    # 3. Start Next.js Ticketing
    if [ -f "$TICKETING_PID" ] && kill -0 $(cat "$TICKETING_PID") 2>/dev/null; then
        echo "✅ SARIP Ticketing ya está corriendo (Port 9999)."
    else
        echo "🚀 Iniciando SARIP Ticketing Frontend (Port 9999)..."
        cd "$TICKETING_DIR"
        nohup npm run dev > ticketing.log 2>&1 &
        echo $! > "$TICKETING_PID"
    fi

    echo "--------------------------------------------------"
    echo "✅ Todos los servicios han sido lanzados."
    echo "   Logs en: [mcp_gateway.log, orchestrator.log, ticketing.log]"
    echo "   Usa './sarip.sh status' para verificar."
}

stop_services() {
    print_header
    echo "Deteniendo servicios de SARIP..."
    
    if [ -f "$TICKETING_PID" ]; then
        kill $(cat "$TICKETING_PID") 2>/dev/null && echo "🛑 SARIP Ticketing detenido."
        rm "$TICKETING_PID"
    fi

    if [ -f "$ORCHESTRATOR_PID" ]; then
        kill $(cat "$ORCHESTRATOR_PID") 2>/dev/null && echo "🛑 LangGraph Orchestrator detenido."
        rm "$ORCHESTRATOR_PID"
    fi

    if [ -f "$MCP_PID" ]; then
        kill $(cat "$MCP_PID") 2>/dev/null && echo "🛑 MCP Gateway detenido."
        rm "$MCP_PID"
    fi
    
    # Fallback to kill by port if PID file failed
    fuser -k 9999/tcp 2>/dev/null
    fuser -k 8000/tcp 2>/dev/null
    fuser -k 8081/tcp 2>/dev/null
    
    echo "✅ Todos los servicios detenidos."
}

status_services() {
    print_header
    echo "Estado actual de los servicios:"
    echo "--------------------------------------------------"
    
    check_status() {
        local pid_file=$1
        local name=$2
        local port=$3
        
        if [ -f "$pid_file" ] && kill -0 $(cat "$pid_file") 2>/dev/null; then
            echo -e "🟢 $name \t [CORRIENDO] (PID: $(cat $pid_file), Puerto: $port)"
        else
            # Double check via port
            if lsof -i :$port > /dev/null; then
                echo -e "🟡 $name \t [CORRIENDO - PID Perdido] (Puerto: $port)"
            else
                echo -e "🔴 $name \t [DETENIDO]"
            fi
        fi
    }

    check_status "$MCP_PID" "MCP Gateway       " "8081"
    check_status "$ORCHESTRATOR_PID" "LangGraph API     " "8000"
    check_status "$TICKETING_PID" "Next.js Ticketing " "9999"
    
    echo "--------------------------------------------------"
    echo "Estado del Core Transaccional (Docker Compose):"
    if [ -d "$TRANSACTIONAL_DIR" ]; then
        cd "$TRANSACTIONAL_DIR"
        docker compose ps --format "table {{.Name}}\t{{.State}}\t{{.Ports}}"
    else
        echo "Directorio transaccional no encontrado."
    fi
    echo "=================================================="
}

# Router command
case "$1" in
    start)
        start_services
        ;;
    start-all)
        run_system "$2"
        start_services
        ;;
    stop)
        stop_services
        ;;
    stop-all)
        stop_services
        stop_core
        ;;
    restart)
        stop_services
        sleep 2
        start_services
        ;;
    status)
        status_services
        ;;
    *)
        echo "Uso incorrecto."
        echo "Comandos válidos: ./sarip.sh {start|start-all|stop|stop-all|status|restart} [horas_de_simulación]"
        exit 1
esac
