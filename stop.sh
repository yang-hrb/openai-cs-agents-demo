#!/bin/bash

# Navigate to the script's directory
cd "$(dirname "$0")"

echo "Stopping Customer Service Agents Demo..."
echo ""

# Check for PIDs file
if [ -f .pids ]; then
    echo "Found .pids file, stopping processes..."
    read BACKEND_PID FRONTEND_PID < .pids

    if [ -n "$BACKEND_PID" ]; then
        echo "Stopping backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null && echo "✓ Backend stopped" || echo "Backend not running"
    fi

    if [ -n "$FRONTEND_PID" ]; then
        echo "Stopping frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID 2>/dev/null && echo "✓ Frontend stopped" || echo "Frontend not running"
    fi

    rm -f .pids
else
    echo "No .pids file found, killing by port..."

    # Kill backend (port 8000)
    if lsof -i :8000 > /dev/null 2>&1; then
        echo "Stopping backend on port 8000..."
        lsof -ti:8000 | xargs kill -9 2>/dev/null
        echo "✓ Backend stopped"
    else
        echo "Backend not running on port 8000"
    fi

    # Kill frontend (port 3000)
    if lsof -i :3000 > /dev/null 2>&1; then
        echo "Stopping frontend on port 3000..."
        lsof -ti:3000 | xargs kill -9 2>/dev/null
        echo "✓ Frontend stopped"
    else
        echo "Frontend not running on port 3000"
    fi
fi

# Clean up log files
if [ -f backend.log ] || [ -f frontend.log ]; then
    read -p "Remove log files? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -f backend.log frontend.log
        echo "✓ Log files removed"
    fi
fi

echo ""
echo "All services stopped!"
