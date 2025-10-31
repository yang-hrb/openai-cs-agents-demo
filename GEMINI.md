# Gemini Code Assistant Context

This document provides context for the Gemini Code Assistant to understand the project structure, technologies used, and how to build and run the application.

## Project Overview

This is a customer service agent demonstration application. It consists of a Python backend and a Next.js frontend.

The backend is a FastAPI application that uses the `openai-agents` library to create a multi-agent system for handling customer service inquiries. The agents are designed to handle specific tasks such as booking seats, checking flight status, and answering frequently asked questions. The backend uses OpenRouter to connect to different language models, including DeepSeek.

The frontend is a Next.js application that provides a chat interface for users to interact with the customer service agents. It displays the conversation, the agent's internal state, and the events that occur during the agent orchestration process.

## Building and Running

### Backend

To build and run the backend, follow these steps:

1.  **Install dependencies:**
    ```bash
    cd python-backend
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **Set environment variables:**

    Create a `.env` file in the `python-backend` directory and add the following environment variable:

    ```
    OPENROUTER_API_KEY=your_openrouter_api_key
    ```

3.  **Run the backend:**
    ```bash
    python -m uvicorn api:app --reload --port 8000
    ```

### Frontend

To build and run the frontend, follow these steps:

1.  **Install dependencies:**
    ```bash
    cd ui
    npm install
    ```

2.  **Run the frontend:**
    ```bash
    npm run dev
    ```

    This command will also start the backend server. The application will be available at `http://localhost:3000`.

## Development Conventions

### Backend

*   The backend is written in Python and uses the FastAPI framework.
*   The agent orchestration logic is defined in `python-backend/main.py`.
*   The API is defined in `python-backend/api.py`.
*   Dependencies are managed with `pip` and are listed in `python-backend/requirements.txt`.

### Frontend

*   The frontend is a Next.js application written in TypeScript.
*   The main page is `ui/app/page.tsx`.
*   Components are located in the `ui/components` directory.
*   The frontend uses Tailwind CSS for styling.
*   Dependencies are managed with `npm` and are listed in `ui/package.json`.
