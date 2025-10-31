#!/bin/bash

# Navigate to the script's directory
cd "$(dirname "$0")"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Customer Service Agents Demo - Startup Script            ║"
echo "║  Using FREE DeepSeek model via OpenRouter                 ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Function to check if a port is in use
check_port() {
    lsof -i :"$1" > /dev/null 2>&1
    return $?
}

# Check if backend is already running
if check_port 8000; then
    echo "⚠️  Backend already running on port 8000"
    read -p "Kill existing backend and restart? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Killing existing backend..."
        lsof -ti:8000 | xargs kill -9 2>/dev/null
        sleep 2
    else
        echo "Keeping existing backend"
    fi
fi

# Check if frontend is already running
if check_port 3000; then
    echo "⚠️  Frontend already running on port 3000"
    read -p "Kill existing frontend and restart? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Killing existing frontend..."
        lsof -ti:3000 | xargs kill -9 2>/dev/null
        sleep 2
    else
        echo "Keeping existing frontend"
    fi
fi

echo ""
echo "Starting services..."
echo ""

# Start backend in background
echo "📦 Starting backend..."
cd python-backend
./start.sh > ../backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Wait for backend to be ready
echo "⏳ Waiting for backend to start..."
for i in {1..30}; do
    if curl -s http://localhost:8000/chat -X POST -H "Content-Type: application/json" -d '{"message":""}' > /dev/null 2>&1; then
        echo "✅ Backend ready on http://localhost:8000"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Backend failed to start. Check backend.log for details"
        exit 1
    fi
    sleep 1
done

# Start frontend in background
echo ""
echo "🌐 Starting frontend..."
cd ui
./start.sh > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Wait for frontend to be ready
echo "⏳ Waiting for frontend to start..."
for i in {1..30}; do
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo "✅ Frontend ready on http://localhost:3000"
        break
    fi
    sleep 1
done

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  🚀 Application is running!                                ║"
echo "╠════════════════════════════════════════════════════════════╣"
echo "║  Frontend: http://localhost:3000                           ║"
echo "║  Backend:  http://localhost:8000                           ║"
echo "║                                                            ║"
echo "║  Logs:                                                     ║"
echo "║    Backend:  tail -f backend.log                           ║"
echo "║    Frontend: tail -f frontend.log                          ║"
echo "║                                                            ║"
echo "║  To stop: Press Ctrl+C or run: ./stop.sh                   ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "PIDs: Backend=$BACKEND_PID Frontend=$FRONTEND_PID"
echo "Saving PIDs to .pids file..."
echo "$BACKEND_PID $FRONTEND_PID" > .pids

# Keep script running
echo ""
echo "Press Ctrl+C to stop all services..."
echo ""

# Trap Ctrl+C
trap "echo ''; echo 'Stopping services...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; rm -f .pids; echo 'Services stopped'; exit 0" INT

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
