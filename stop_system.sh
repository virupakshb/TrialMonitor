#!/bin/bash

# Clinical Trial Rules Engine - Stop Script

echo "🛑 Stopping Clinical Trial Rules Engine..."

if [ -f ".pids" ]; then
    while read pid; do
        if ps -p $pid > /dev/null 2>&1; then
            echo "   Stopping process $pid..."
            kill $pid 2>/dev/null
        fi
    done < .pids
    rm .pids
    echo "✓ All services stopped"
else
    echo "⚠️  No PID file found. Services may still be running."
    echo "   Use: ps aux | grep -E 'uvicorn|vite' to find processes"
fi

# Clean up log files
if [ -f "backend.log" ]; then
    rm backend.log
fi
if [ -f "frontend.log" ]; then
    rm frontend.log
fi

echo "✓ Cleanup complete"
