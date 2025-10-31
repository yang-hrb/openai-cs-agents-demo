# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a customer service agent demo application that demonstrates multi-agent orchestration using the OpenAI Agents SDK, configured to use OpenRouter API with DeepSeek models instead of OpenAI's GPT models. The application consists of:

1. **Python backend** (`python-backend/`): FastAPI server handling agent orchestration logic
2. **Next.js UI** (`ui/`): React/TypeScript frontend with real-time visualization of agent orchestration

## Commands

### Quick Start (Both Backend + Frontend)

The easiest way to run everything:

```bash
# From project root - starts both backend and frontend
./start.sh

# To stop everything
./stop.sh
```

This will:
- Start backend on http://localhost:8000
- Start frontend on http://localhost:3000
- Save logs to `backend.log` and `frontend.log`
- Handle port conflicts automatically

### Backend Development

```bash
# Navigate to backend
cd python-backend

# Quick start (recommended - handles venv setup automatically)
./start.sh

# Or manual setup:
# Create and activate virtual environment (first time only)
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run backend independently
python -m uvicorn api:app --reload --port 8000
# Backend available at http://localhost:8000
```

### Frontend Development

```bash
# Navigate to UI
cd ui

# Quick start (recommended - handles npm install automatically)
./start.sh

# Or manual setup:
# Install dependencies
npm install

# Run UI only (Next.js dev server)
npm run dev:next
# Frontend available at http://localhost:3000

# Run both UI and backend simultaneously
npm run dev

# Build for production
npm run build

# Run linter
npm run lint
```

### API Key Configuration

This application uses OpenRouter with FREE DeepSeek models:

**Option 1: Use .env file (recommended)**
```bash
# Edit the .env file in python-backend/
cd python-backend
# Open .env and replace 'your_openrouter_api_key_here' with your actual key
```

**Option 2: Environment variable**
```bash
export OPENROUTER_API_KEY=your_openrouter_api_key
```

Get your free API key at: https://openrouter.ai/keys

**Note**: The `.env` file is already in `.gitignore` and won't be committed to git.

**Current Model**: `deepseek/deepseek-chat:free` (100% free via OpenRouter)

**Other Free Model Options** (change `MODEL_NAME` in `main.py`):
- `deepseek/deepseek-r1:free` - Latest reasoning model (671B params)
- `deepseek/deepseek-r1-distill-llama-70b:free` - Distilled 70B version
- `deepseek/deepseek-r1-distill-qwen-14b:free` - Distilled 14B version
- `openai/gpt-oss-20b:free` - OpenAI's open-weight 20B model
- `openai/gpt-oss-120b:free` - OpenAI's open-weight 120B MoE model

**Technical Note**: The application configures a custom AsyncOpenAI client pointing to OpenRouter's API, which bypasses the Agents SDK's model prefix parsing limitations.

## Architecture

### Backend Architecture (`python-backend/`)

**Entry Point**: `api.py` - FastAPI application with single `/chat` endpoint

**Core Components**:
- `main.py` - Agent definitions, tools, guardrails, and context management
- `api.py` - HTTP layer, conversation state management, event processing

**Agent System**:
The application uses a multi-agent orchestration pattern with five specialized agents:

1. **Triage Agent** - Entry point that routes requests to specialist agents
2. **Seat Booking Agent** - Handles seat changes (tools: `update_seat`, `display_seat_map`)
3. **Flight Status Agent** - Provides flight information (tool: `flight_status_tool`)
4. **Cancellation Agent** - Processes flight cancellations (tool: `cancel_flight`)
5. **FAQ Agent** - Answers general questions (tool: `faq_lookup_tool`)

**Handoff System**:
- Agents can transfer conversations to other agents via the `handoff()` function
- Handoffs can include callbacks (`on_handoff`) that execute during transfer
- Example: `on_seat_booking_handoff` generates random flight/confirmation numbers
- All specialist agents can handoff back to the Triage Agent

**Guardrails**:
Two input guardrails protect all agents:
- **Relevance Guardrail**: Ensures questions are airline-related
- **Jailbreak Guardrail**: Detects prompt injection attempts
- Both use DeepSeek model to evaluate inputs and can trigger conversation refusals

**Context Management**:
- `AirlineAgentContext` (Pydantic model) tracks conversation state:
  - `passenger_name`, `confirmation_number`, `seat_number`, `flight_number`, `account_number`
- Context is passed through all agent interactions
- Tools can read/write context via `RunContextWrapper[AirlineAgentContext]`
- Context changes are tracked and sent to UI as events

**Conversation State**:
- `InMemoryConversationStore` maintains conversation history (NOTE: not production-ready)
- Each conversation has unique ID and persists: input items, context, current agent
- For production, replace with Redis/database-backed store

**Model Configuration**:
- All agents use `deepseek/deepseek-chat:free` (free via OpenRouter)
- Custom AsyncOpenAI client configured in `main.py` pointing to OpenRouter
- Client is set as default before Agent SDK loads, bypassing prefix parsing
- To switch models: change `MODEL_NAME` variable in `main.py:53`
- Supports any OpenRouter model identifier including `provider/model:tier` format

### Frontend Architecture (`ui/`)

**Entry Point**: `app/page.tsx` - Main chat interface (Next.js App Router)

**State Management**:
- React `useState` hooks manage: messages, events, agents, guardrails, context, conversation ID
- `callChatAPI()` in `lib/api.ts` handles backend communication
- UI boots conversation with empty message to initialize state

**Key Components**:
- `Chat.tsx` - Message display and input handling
- `agent-panel.tsx` - Right sidebar showing agent orchestration
- `runner-output.tsx` - Event stream visualization (tool calls, handoffs, etc.)
- `guardrails.tsx` - Real-time guardrail status indicators
- `seat-map.tsx` - Interactive seat selection component
- `conversation-context.tsx` - Context state display

**Event System**:
Backend sends typed events that drive UI updates:
- `message` - Agent responses
- `handoff` - Agent-to-agent transfers (visualized with source → target)
- `tool_call` - Function executions
- `tool_output` - Tool results
- `context_update` - State changes

**Special UI Interactions**:
- When `display_seat_map` tool is called, UI renders interactive seat selector
- Seat selection sends chosen seat back to backend in next message
- Guardrail failures show red indicators in sidebar

**TypeScript Types** (`lib/types.ts`):
Core interfaces: `Message`, `Agent`, `AgentEvent`, `GuardrailCheck`

## Key Implementation Details

### Adding New Agents

1. Define agent in `main.py` with: name, model, instructions, tools, guardrails
2. Add to `_get_agent_by_name()` dictionary in `api.py`
3. Include in `_build_agents_list()` in `api.py`
4. Set up handoff relationships (bidirectional if needed)

### Adding New Tools

1. Decorate function with `@function_tool` in `main.py`
2. Tools can accept `RunContextWrapper[AirlineAgentContext]` to access/modify context
3. Add tool to appropriate agent's `tools=[]` list
4. If tool needs special UI handling, update `api.py` event processing

### Modifying Context Schema

1. Update `AirlineAgentContext` Pydantic model in `main.py`
2. Context changes automatically propagate to all agents
3. UI receives context updates via `context_update` events

### Testing Specific Flows

The README documents two demo flows:
1. Seat change → Flight status → FAQ
2. Flight cancellation → Guardrail triggers

Use these as integration test scenarios when making changes.

## Important Notes

- All agents use `deepseek/deepseek-chat:free` - **100% FREE** via OpenRouter
- Backend runs on port 8000, frontend on port 3000
- CORS is configured for `http://localhost:3000` only
- Conversation store is in-memory - data lost on restart
- The `npm run dev` command in `ui/` starts both frontend and backend via `concurrently`
- Custom OpenAI client configuration in `main.py:33-43` enables OpenRouter model names
- Get free OpenRouter API key at https://openrouter.ai/keys
