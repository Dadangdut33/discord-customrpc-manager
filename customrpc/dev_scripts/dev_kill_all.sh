#!/bin/bash

# Development script to kill all running CustomRPCManager instances
# Useful when the app bugs out and the window/tray is not visible

echo "🔍 Searching for CustomRPCManager processes..."

# Check lock and port files
LOCK_FILE="$HOME/.config/customrpcmanager/.lock"
PORT_FILE="$HOME/.config/customrpcmanager/.port"

if [ -f "$LOCK_FILE" ]; then
    LOCK_PID=$(cat "$LOCK_FILE" 2>/dev/null)
    if [ -n "$LOCK_PID" ]; then
        echo "📄 Lock file PID: $LOCK_PID"
    fi
fi

if [ -f "$PORT_FILE" ]; then
    PORT=$(cat "$PORT_FILE" 2>/dev/null)
    if [ -n "$PORT" ]; then
        echo "📄 IPC Port: $PORT"
    fi
fi

echo ""

# Find all python processes running customrpcmanager
PIDS=$(ps aux | grep -E "python.*customrpcmanager|customrpcmanager.*main.py" | grep -v grep | awk '{print $2}')

if [ -z "$PIDS" ]; then
    echo "✅ No CustomRPCManager processes found running."
    
    # Still clean up lock files if they exist
    if [ -f "$LOCK_FILE" ] || [ -f "$PORT_FILE" ]; then
        echo ""
        echo "🧹 Cleaning up stale lock and port files..."
        rm -f "$LOCK_FILE" 2>/dev/null && echo "  ✓ Removed lock file"
        rm -f "$PORT_FILE" 2>/dev/null && echo "  ✓ Removed port file"
    fi
    
    exit 0
fi

echo "📋 Found the following CustomRPCManager processes:"
ps aux | grep -E "python.*customrpcmanager|customrpcmanager.*main.py" | grep -v grep

# Count processes
COUNT=$(echo "$PIDS" | wc -w)
echo ""
echo "🎯 Found $COUNT process(es) to kill"

# Kill each process
for PID in $PIDS; do
    echo "🔪 Killing process $PID..."
    kill -TERM $PID 2>/dev/null
    
    # Wait a bit for graceful shutdown
    sleep 0.5
    
    # Check if process is still running
    if ps -p $PID > /dev/null 2>&1; then
        echo "⚠️  Process $PID didn't respond to SIGTERM, sending SIGKILL..."
        kill -KILL $PID 2>/dev/null
    fi
done

# Wait a moment and verify
sleep 1
echo ""
echo "🔍 Verifying all processes are killed..."
REMAINING=$(ps aux | grep -E "python.*customrpcmanager|customrpcmanager.*main.py" | grep -v grep | wc -l)

if [ "$REMAINING" -eq 0 ]; then
    echo "✅ All CustomRPCManager processes have been terminated!"
else
    echo "⚠️  Some processes may still be running:"
    ps aux | grep -E "python.*customrpcmanager|customrpcmanager.*main.py" | grep -v grep
fi

# Clean up lock and port files
echo ""
echo "🧹 Cleaning up lock and port files..."
if [ -d "$HOME/.config/customrpcmanager" ]; then
    rm -f "$HOME/.config/customrpcmanager/.lock" 2>/dev/null && echo "  ✓ Removed lock file"
    rm -f "$HOME/.config/customrpcmanager/.port" 2>/dev/null && echo "  ✓ Removed port file"
fi

echo ""
echo "🎉 Done!"
