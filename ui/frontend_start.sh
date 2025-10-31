#!/bin/bash

# Navigate to the script's directory
cd "$(dirname "$0")"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "node_modules not found. Installing dependencies..."
    npm install
fi

# Check if backend is running
echo "Checking if backend is running..."
if curl -s http://localhost:8000/chat -X POST -H "Content-Type: application/json" -d '{"message":""}' > /dev/null 2>&1; then
    echo "✓ Backend is running on http://localhost:8000"
else
    echo ""
    echo "⚠️  WARNING: Backend doesn't appear to be running!"
    echo "   Start it first with: cd ../python-backend && ./start.sh"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "Starting frontend on http://localhost:3000..."
echo "The frontend will be available at: http://localhost:3000"
echo "Press Ctrl+C to stop"
echo ""

npm run dev:next
