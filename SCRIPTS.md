# Startup Scripts Reference

## Quick Start

The fastest way to get everything running:

```bash
./start.sh
```

This single command will:
- ✅ Start the backend with FREE DeepSeek model
- ✅ Start the frontend Next.js app
- ✅ Check for port conflicts
- ✅ Wait for services to be ready
- ✅ Save logs to `backend.log` and `frontend.log`

Access the app at: **http://localhost:3000**

---

## Individual Services

### Backend Only

```bash
cd python-backend
./start.sh
```

Features:
- Auto-creates virtual environment if missing
- Installs dependencies automatically
- Loads API key from `.env` file
- Warns if `OPENROUTER_API_KEY` not set
- Runs on http://localhost:8000

### Frontend Only

```bash
cd ui
./start.sh
```

Features:
- Auto-installs npm dependencies if missing
- Checks if backend is running
- Prompts to continue if backend is down
- Runs on http://localhost:3000

---

## Stopping Services

### Stop Everything

```bash
./stop.sh
```

This will:
- Stop both backend and frontend
- Kill processes by PID or port
- Optionally clean up log files

### Manual Stop

```bash
# Kill backend
lsof -ti:8000 | xargs kill

# Kill frontend
lsof -ti:3000 | xargs kill
```

---

## Logs

View logs in real-time:

```bash
# Backend logs
tail -f backend.log

# Frontend logs
tail -f frontend.log

# Both logs
tail -f backend.log frontend.log
```

---

## Configuration

### API Key Setup

Edit `python-backend/.env`:
```bash
OPENROUTER_API_KEY=your_key_here
```

Get your free key at: https://openrouter.ai/keys

### Change Model

Edit `python-backend/main.py` line 53:
```python
MODEL_NAME = "deepseek/deepseek-chat:free"  # Current

# Or try:
# MODEL_NAME = "deepseek/deepseek-r1:free"  # Latest reasoning model
# MODEL_NAME = "openai/gpt-oss-20b:free"    # OpenAI's 20B model
```

All models are FREE via OpenRouter!

---

## Troubleshooting

### Port Already In Use

```bash
# Check what's using the port
lsof -i :8000  # Backend
lsof -i :3000  # Frontend

# Kill the process
kill -9 <PID>
```

### Backend Won't Start

1. Check if API key is set: `cat python-backend/.env`
2. Verify venv exists: `ls python-backend/.venv`
3. Check logs: `cat backend.log`

### Frontend Won't Connect

1. Verify backend is running: `curl http://localhost:8000/chat -X POST -d '{"message":""}'`
2. Check CORS settings in `python-backend/api.py` (line 36-42)
3. Check frontend logs: `cat frontend.log`

---

## Development Tips

### Backend Development

```bash
cd python-backend
source .venv/bin/activate  # Activate venv
python -m uvicorn api:app --reload --port 8000  # Manual start
```

### Frontend Development

```bash
cd ui
npm run dev:next  # Just frontend
npm run dev       # Frontend + backend together
```

### Code Changes

- Backend auto-reloads on file changes (uvicorn --reload)
- Frontend auto-reloads via Next.js Fast Refresh
- No need to restart for most code changes!
