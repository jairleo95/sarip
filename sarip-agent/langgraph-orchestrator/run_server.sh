#!/bin/bash

# Configuration
PROJECT_DIR="/home/darkstar/Workspace/dev/service-payment/sarip-agent/langgraph-orchestrator"
VENV_DIR="$PROJECT_DIR/.venv"
SERVER_SCRIPT="server.py"

echo "=================================================="
echo "🚀 Iniciando SARIP LangGraph Orchestrator Server"
echo "=================================================="

# Navigate to the project directory
cd "$PROJECT_DIR" || { echo "Error: Directorio del proyecto no encontrado"; exit 1; }

# Check if the virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "⚠️  Entorno virtual no encontrado en $VENV_DIR"
    echo "⚙️  Creando entorno virtual e instalando dependencias..."
    python3 -m venv .venv
    
    # Activate and install
    source "$VENV_DIR/bin/activate"
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    else
        echo "⚠️  Advertencia: requirements.txt no encontrado."
    fi
else
    # Activate the existing virtual environment
    echo "✅ Entorno virtual detectado. Activando..."
    source "$VENV_DIR/bin/activate"
fi

# Ensure .env exists (copy from example if missing)
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "⚠️  Archivo .env no encontrado. Creando base desde .env.example..."
        cp .env.example .env
        echo "⛔ IMPORTANTE: Edita el archivo .env para agregar tus API Keys antes del primer uso real."
    fi
fi

echo "🟢 Ejecutando servidor..."
echo "--------------------------------------------------"

# Run the server
python "$SERVER_SCRIPT"
