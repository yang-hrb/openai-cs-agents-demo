#!/bin/bash

# Navigate to the script's directory
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Creating it..."
    python -m venv .venv
    echo "Installing dependencies..."
    .venv/bin/pip install -r requirements.txt
fi

# Check if OPENROUTER_API_KEY is set
if [ -z "$OPENROUTER_API_KEY" ] && [ ! -f ".env" ]; then
    echo "WARNING: OPENROUTER_API_KEY not set and no .env file found."
    echo "You may need to set your API key for the agents to work properly."
    echo ""
    echo "Set it with: export OPENROUTER_API_KEY=your_key"
    echo "Or create a .env file with: echo 'OPENROUTER_API_KEY=your_key' > .env"
    echo ""
fi

# Start the backend
echo "Starting backend server on http://localhost:8000..."
.venv/bin/python -m uvicorn api:app --reload --port 8000
