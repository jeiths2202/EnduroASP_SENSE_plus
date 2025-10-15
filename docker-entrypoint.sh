#!/bin/bash
# Docker Container Entrypoint Script for OpenASP AX

echo "========================================="
echo "Docker Container Starting..."
echo "========================================="

# Set environment variables
export APP_ROOT="/home/aspuser/app"
export PATH="$PATH:$APP_ROOT"

# Wait for PostgreSQL to be ready (if needed)
echo "Checking PostgreSQL availability..."
for i in {1..30}; do
    if pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
        echo "PostgreSQL is ready!"
        break
    fi
    echo "Waiting for PostgreSQL... ($i/30)"
    sleep 2
done

# Change to app directory
cd "$APP_ROOT"

# Execute master-start.sh
echo "Starting OpenASP AX services..."
if [ -f "$APP_ROOT/master-start.sh" ]; then
    # Make sure the script is executable
    chmod +x "$APP_ROOT/master-start.sh"
    chmod +x "$APP_ROOT/master-stop.sh"
    
    # Start services
    "$APP_ROOT/master-start.sh"
    
    echo "========================================="
    echo "OpenASP AX services started successfully!"
    echo "========================================="
    
    # Keep container running
    echo "Container is ready. Press Ctrl+C to stop."
    
    # Trap signals to gracefully shutdown
    trap "$APP_ROOT/master-stop.sh; exit 0" SIGTERM SIGINT
    
    # Keep the container alive
    tail -f /dev/null
else
    echo "ERROR: master-start.sh not found!"
    exit 1
fi