#!/bin/bash
# OpenASP Refactor Chat Service Shutdown Script
# チャットサービス（Ollama + Chat API）停止スクリプト

echo "[CHAT] OpenASP Chat Service Shutdown..."
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
PID_DIR="$PROJECT_ROOT/pids"
BITNET_DIR="/home/aspuser/app/models/bitnet/BitNet"

# UTF-8 encoding environment variables
export LC_ALL=C.UTF-8
export LANG=C.UTF-8
export PYTHONIOENCODING=utf-8

# Force kill processes by pattern
force_kill_by_pattern() {
    local pattern="$1"
    local description="$2"
    
    echo -n "$description shutdown... "
    
    # Try graceful termination with SIGTERM first
    pkill -f "$pattern" 2>/dev/null || true
    sleep 2
    
    # Force kill with SIGKILL if still running
    pkill -9 -f "$pattern" 2>/dev/null || true
    
    echo -e "${GREEN}[OK]${NC}"
}

# Force kill processes by port
force_kill_by_port() {
    local port="$1"
    local description="$2"
    
    echo -n "$description (Port $port) shutdown... "
    
    # Find processes using the port
    local pids=$(lsof -ti:$port 2>/dev/null || true)
    
    if [ ! -z "$pids" ]; then
        # Try SIGTERM first
        echo "$pids" | xargs -r kill 2>/dev/null || true
        sleep 2
        
        # Force kill if still running
        local remaining_pids=$(lsof -ti:$port 2>/dev/null || true)
        if [ ! -z "$remaining_pids" ]; then
            echo "$remaining_pids" | xargs -r kill -9 2>/dev/null || true
        fi
    fi
    
    echo -e "${GREEN}[OK]${NC}"
}

# Stop services by PID (or Docker container ID)
stop_by_pid() {
    local pid_file="$1"
    local description="$2"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file" 2>/dev/null)
        if [ ! -z "$pid" ]; then
            if kill -0 "$pid" 2>/dev/null; then
                echo -n "$description (PID $pid) shutdown... "
                # Try graceful termination first
                kill "$pid" 2>/dev/null || true
                sleep 2
                
                # Force kill if still running
                if kill -0 "$pid" 2>/dev/null; then
                    kill -9 "$pid" 2>/dev/null || true
                fi
                echo -e "${GREEN}[OK]${NC}"
            fi
        fi
        rm -f "$pid_file"
    fi
}

echo -e "\n${YELLOW}Shutting down chat services...${NC}"

# Stop by PID files first
stop_by_pid "$PID_DIR/ollama.pid" "Ollama Server"
stop_by_pid "$PID_DIR/chat-api.pid" "Chat API Server"
stop_by_pid "$PID_DIR/bitnet.pid" "BitNet Service"

# Stop by process patterns
echo -e "\n${YELLOW}Shutting down processes by pattern...${NC}"
force_kill_by_pattern "ollama serve" "Ollama Servers"
force_kill_by_pattern "ollama runner" "Ollama Runners"
force_kill_by_pattern "chat_api.py" "Chat API Servers"
force_kill_by_pattern "hf download" "BitNet Downloads"
force_kill_by_pattern "llama-cli" "BitNet Inference"

# Stop by ports
echo -e "\n${YELLOW}Force killing processes by port...${NC}"
force_kill_by_port "$OLLAMA_PORT" "Ollama Server"
force_kill_by_port "$CHAT_API_PORT" "Chat API Server"

# Cleanup files
echo -e "\n${YELLOW}Cleaning up configuration files...${NC}"
rm -f "$PROJECT_ROOT/.chat_services"
rm -f "$PID_DIR/ollama.pid"
rm -f "$PID_DIR/chat-api.pid"
rm -f "$PID_DIR/bitnet.pid"

# Wait for process termination
echo -e "\n${YELLOW}Waiting for process termination...${NC}"
sleep 3

# Final port status check
echo -e "\n${YELLOW}Final port status check...${NC}"
all_clear=true

for port in $OLLAMA_PORT $CHAT_API_PORT; do
    if lsof -i :$port > /dev/null 2>&1; then
        echo -e "${RED}[WARN] Port $port still in use${NC}"
        all_clear=false
        
        # Final attempt to force kill
        local final_pids=$(lsof -ti:$port 2>/dev/null || true)
        if [ ! -z "$final_pids" ]; then
            echo "  Final force kill attempt..."
            echo "$final_pids" | xargs -r kill -9 2>/dev/null || true
        fi
    else
        echo -e "${GREEN}[OK] Port $port released${NC}"
    fi
done

echo ""
echo "========================================="
if [ "$all_clear" = true ]; then
    echo -e "${GREEN}[DONE] Chat Service completely shutdown.${NC}"
else
    echo -e "${YELLOW}[WARN] Some chat service ports are still in use.${NC}"
    echo -e "${YELLOW}       You may need to restart the system.${NC}"
fi
echo ""