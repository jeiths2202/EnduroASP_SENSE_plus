#!/bin/bash

# OpenASP DevOps Server Startup Script
# This script ensures the server stays running until manually stopped

echo "🚀 Starting OpenASP DevOps Server..."
echo "📊 Access Dashboard at: http://localhost:3016"
echo "🔧 Press Ctrl+C to stop the server"

cd /home/aspuser/app/ofasp-devops

# Function to handle cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down OpenASP DevOps Server..."
    kill $SERVER_PID 2>/dev/null
    wait $SERVER_PID 2>/dev/null
    echo "✅ Server stopped successfully"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start the development server in background
npm run dev &
SERVER_PID=$!

echo "🎯 Server PID: $SERVER_PID"
echo "⏱️  Server will run continuously until you stop it"

# Keep the script running and monitor server
while kill -0 $SERVER_PID 2>/dev/null; do
    sleep 5
done

# If we get here, the server died unexpectedly
echo "❌ Server process died unexpectedly, restarting..."
exec $0