# Product Requirements Document: Customer Service Agents Demo

## 1. Introduction

This document outlines the product requirements for a customer service agent demonstration application. The application showcases a multi-agent system that can handle various customer inquiries for an airline. The existing implementation uses a Python backend with the `openai-agents` library and a Next.js frontend. A key requirement for the project is to leverage Large Language Models (LLMs) available through OpenRouter, specifically avoiding direct integration with the OpenAI API to minimize costs.

## 2. Goals and Objectives

*   **Primary Goal:** To create a robust and extensible customer service agent demo that showcases the power of a multi-agent system for customer support.
*   **Key Objective 1:** To use a cost-effective LLM from OpenRouter (such as DeepSeek or a suitable alternative) for all agent operations, ensuring no reliance on the paid OpenAI API.
*   **Key Objective 2:** To provide a clear and intuitive user interface for customers to interact with the agents.
*   **Key Objective 3:** To build a flexible and modular backend that allows for easy addition of new agents, tools, and guardrails.

## 3. Target Audience

*   **Developers and Product Managers:** To understand how a multi-agent system can be implemented for customer service applications.
*   **Potential Customers:** To see a demonstration of an AI-powered customer service solution.

## 4. Features and Functionality

### 4.1. Core Features

*   **Chat Interface:** A web-based chat interface for users to interact with the customer service agents.
*   **Agent Orchestration:** A backend system that manages a team of specialized AI agents and routes user requests to the appropriate agent.
*   **Triage Agent:** A primary agent that receives all user requests and delegates them to the appropriate specialist agent.
*   **Specialist Agents:**
    *   **Seat Booking Agent:** Handles seat change requests.
    *   **Flight Status Agent:** Provides flight status information.
    *   **Cancellation Agent:** Processes flight cancellations.
    *   **FAQ Agent:** Answers frequently asked questions.
*   **Agent Tools:** Each agent has a set of tools to perform its tasks, such as:
    *   `faq_lookup_tool`: Looks up answers to frequently asked questions.
    *   `update_seat`: Updates a passenger's seat.
    *   `flight_status_tool`: Retrieves the status of a flight.
    *   `baggage_tool`: Provides information about baggage allowance and fees.
    *   `display_seat_map`: Triggers the UI to display an interactive seat map.
    *   `cancel_flight`: Cancels a flight.
*   **Guardrails:** Input guardrails to ensure the conversation remains on-topic and to prevent prompt injection attacks.
    *   **Relevance Guardrail:** Checks if the user's message is relevant to airline customer service.
    *   **Jailbreak Guardrail:** Detects attempts to bypass system instructions.
*   **Agent View:** A UI panel that visualizes the agent orchestration process, including the current agent, events, guardrail checks, and conversation context.

### 4.2. New Requirements and Modifications

*   **LLM Flexibility:** The system must be configurable to use different LLMs from OpenRouter. The default model should be a cost-effective model with strong performance, such as `deepseek/deepseek-chat` or `google/gemini-flash-1.5`.
*   **Configuration File:** Introduce a configuration file (e.g., `config.yaml` or `settings.py`) to manage agent definitions, model names, and other settings, instead of hardcoding them in `main.py`.
*   **Enhanced Tools:**
    *   **Real-time Flight Status:** The `flight_status_tool` should be updated to integrate with a mock (or real) flight status API to provide more dynamic and realistic responses.
    *   **Persistent Seat Map:** The `update_seat` tool should interact with a more persistent representation of the seat map, so that changes are reflected across user sessions (for demonstration purposes).
*   **Expanded Guardrails:**
    *   **PII Detection:** Add a guardrail to detect and redact Personally Identifiable Information (PII) from user messages.
    *   **Sentiment Analysis:** Implement a guardrail to analyze the sentiment of user messages and escalate to a human agent if the user becomes frustrated.

## 5. Technical Requirements

*   **Backend:**
    *   **Framework:** Python with FastAPI.
    *   **Agent Library:** `openai-agents`.
    *   **LLM Integration:** OpenRouter API.
*   **Frontend:**
    *   **Framework:** Next.js with React.
    *   **Language:** TypeScript.
    *   **Styling:** Tailwind CSS.
*   **LLM:**
    *   **Default Model:** `deepseek/deepseek-chat` (or a similar cost-effective model from OpenRouter).
    *   **Model Configuration:** The model should be easily configurable without code changes.

## 6. Out of Scope

*   **Human Agent Handoff:** While sentiment analysis is in scope, the actual handoff to a human agent will not be implemented in this demo.
*   **User Authentication:** The demo will not include user authentication or accounts.
*   **Production-Ready Database:** The conversation history will be stored in memory and will not be persisted to a production-grade database.

## 7. Success Metrics

*   **Cost-Effectiveness:** The application should be able to handle a high volume of requests with minimal cost by using a non-OpenAI model from OpenRouter.
*   **Performance:** The agents should respond to user queries with low latency.
*   **Accuracy:** The agents should provide accurate and helpful information to users.
*   **Extensibility:** The system should be easy to extend with new agents, tools, and guardrails.
