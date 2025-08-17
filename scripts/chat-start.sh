#!/bin/bash
# OpenASP Refactor Chat Service Startup Script
# チャットサービス（Ollama + Chat API）起動スクリプト

echo "[CHAT] OpenASP Chat Service Startup..."
echo "========================================="

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
OLLAMA_PORT=3014
CHAT_API_PORT=3006
PROJECT_ROOT="/home/aspuser/app/ofasp-refactor"
LOG_DIR="$PROJECT_ROOT/logs"
PID_DIR="$PROJECT_ROOT/pids"
RAG_DIR="$PROJECT_ROOT/public/RAG"

# Create directories
mkdir -p "$LOG_DIR"
mkdir -p "$PID_DIR"
mkdir -p "$RAG_DIR"

# Cleanup existing chat processes
cleanup_chat_processes() {
    echo -e "${YELLOW}[CLEANUP] Stopping existing chat processes...${NC}"
    
    # Stop Ollama server
    pkill -f "ollama serve" 2>/dev/null || true
    pkill -f "ollama runner" 2>/dev/null || true
    
    # Stop Chat API
    pkill -f "chat_api.py" 2>/dev/null || true
    
    # Stop by PID files
    for pid_file in "$PID_DIR/ollama.pid" "$PID_DIR/chat-api.pid"; do
        if [ -f "$pid_file" ]; then
            local pid=$(cat "$pid_file" 2>/dev/null)
            if [ ! -z "$pid" ] && ps -p $pid > /dev/null 2>&1; then
                echo "  Stopping process (PID: $pid)..."
                kill -TERM $pid 2>/dev/null || true
                sleep 2
                if ps -p $pid > /dev/null 2>&1; then
                    kill -9 $pid 2>/dev/null || true
                fi
            fi
            rm -f "$pid_file"
        fi
    done
    
    # Kill processes by port
    for port in $OLLAMA_PORT $CHAT_API_PORT; do
        local pids=$(lsof -ti:$port 2>/dev/null || true)
        if [ ! -z "$pids" ]; then
            echo "  Killing processes on port $port..."
            echo "$pids" | xargs -r kill -9 2>/dev/null || true
        fi
    done
    
    sleep 2
}

# Start Ollama server
start_ollama() {
    echo -e "\n${GREEN}[OLLAMA] Starting Ollama server on port $OLLAMA_PORT...${NC}"
    
    # Initialize log
    > "$LOG_DIR/ollama.log"
    
    # Start Ollama with specific host and port
    OLLAMA_HOST=0.0.0.0:$OLLAMA_PORT ollama serve > "$LOG_DIR/ollama.log" 2>&1 &
    local pid=$!
    
    # Save PID
    echo "$pid" > "$PID_DIR/ollama.pid"
    echo "Ollama PID: $pid"
    
    # Wait for Ollama to start
    local count=0
    local max_wait=30
    while [ $count -lt $max_wait ]; do
        if curl -s http://localhost:$OLLAMA_PORT/api/tags >/dev/null 2>&1; then
            echo -e "${GREEN}[OK] Ollama server ready${NC}"
            return 0
        fi
        sleep 2
        count=$((count + 2))
        if [ $((count % 10)) -eq 0 ]; then
            echo "  Ollama waiting... ($count/${max_wait}sec)"
        fi
    done
    
    echo -e "${RED}[NG] Ollama startup failed${NC}"
    return 1
}

# Start Chat API
start_chat_api() {
    echo -e "\n${GREEN}[API] Starting Chat API server on port $CHAT_API_PORT...${NC}"
    
    cd "$PROJECT_ROOT/server"
    
    # Initialize log
    > "$LOG_DIR/chat-api.log"
    
    # Set environment variables and start Chat API
    CHAT_API_PORT=$CHAT_API_PORT \
    OLLAMA_URL=http://localhost:$OLLAMA_PORT \
    RAG_DIR="$RAG_DIR" \
    python3 chat_api.py > "$LOG_DIR/chat-api.log" 2>&1 &
    local pid=$!
    
    # Save PID
    echo "$pid" > "$PID_DIR/chat-api.pid"
    echo "Chat API PID: $pid"
    
    # Wait for Chat API to start
    local count=0
    local max_wait=30
    while [ $count -lt $max_wait ]; do
        if curl -s http://localhost:$CHAT_API_PORT/api/health >/dev/null 2>&1; then
            echo -e "${GREEN}[OK] Chat API server ready${NC}"
            return 0
        fi
        sleep 2
        count=$((count + 2))
        if [ $((count % 10)) -eq 0 ]; then
            echo "  Chat API waiting... ($count/${max_wait}sec)"
        fi
    done
    
    echo -e "${RED}[NG] Chat API startup failed${NC}"
    return 1
}


# Check available models
check_models() {
    echo -e "\n${YELLOW}[MODELS] Checking available models...${NC}"
    
    # Get available models
    local models=$(curl -s http://localhost:$OLLAMA_PORT/api/tags | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    models = [m['name'] for m in data.get('models', [])]
    for model in models:
        print(f'  - {model}')
except:
    pass
" 2>/dev/null)
    
    if [ ! -z "$models" ]; then
        echo -e "${GREEN}Available models:${NC}"
        echo "$models"
    else
        echo -e "${YELLOW}No models found. You may need to install models:${NC}"
        echo "  ollama pull gemma:2b"
        echo "  ollama pull gpt-oss:20b"
        echo "  ollama pull qwen2.5-coder:1.5b"
    fi
}

# Main execution
main() {
    cleanup_chat_processes
    
    if start_ollama && start_chat_api; then
        check_models
        
        echo -e "\n========================================="
        echo -e "${GREEN}[DONE] Chat Service startup complete!${NC}"
        echo ""
        echo "[ACCESS] Service URLs:"
        echo "  - Chat Interface: http://localhost:3005 → チャット"
        echo "  - Chat API: http://localhost:$CHAT_API_PORT"
        echo "  - Ollama API: http://localhost:$OLLAMA_PORT"
        
        echo ""
        echo "[LOGS] Log files:"
        echo "  - Ollama: $LOG_DIR/ollama.log"
        echo "  - Chat API: $LOG_DIR/chat-api.log"
        
        echo ""
        echo "[STOP] Shutdown command:"
        echo "  $PROJECT_ROOT/scripts/chat-stop.sh"
        echo ""
        
        # Save service info
        cat > "$PROJECT_ROOT/.chat_services" << EOF
OLLAMA_PID=$(cat $PID_DIR/ollama.pid)
CHAT_API_PID=$(cat $PID_DIR/chat-api.pid)
OLLAMA_PORT=$OLLAMA_PORT
CHAT_API_PORT=$CHAT_API_PORT
STARTED_AT="$(date)"
EOF
        
        return 0
    else
        echo -e "\n${RED}[NG] Chat Service startup failed!${NC}"
        echo "Check log files for details:"
        echo "  - $LOG_DIR/ollama.log"
        echo "  - $LOG_DIR/chat-api.log"
        return 1
    fi
}

# Execute main function
main "$@"