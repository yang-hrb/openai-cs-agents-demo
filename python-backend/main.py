from __future__ import annotations

import json
import random
import string
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from perplexity_client import chat, extract_text_choice

# =========================
# CONTEXT MODELS
# =========================


class AirlineAgentContext(BaseModel):
    """Context for airline customer service agents."""

    passenger_name: Optional[str] = None
    confirmation_number: Optional[str] = None
    seat_number: Optional[str] = None
    flight_number: Optional[str] = None
    account_number: Optional[str] = None


class ConversationState(BaseModel):
    """Runtime state stored for each conversation."""

    context: AirlineAgentContext
    history: List[Dict[str, Any]] = Field(default_factory=list)
    current_agent: str = "Triage Agent"


@dataclass
class ToolInvocation:
    name: str
    arguments: Dict[str, Any]
    result: Optional[str] = None


@dataclass
class AgentRunResult:
    messages: List[str]
    handoff: Optional[str]
    tool_calls: List[ToolInvocation]


@dataclass
class GuardrailDecision:
    name: str
    passed: bool
    reasoning: str


# =========================
# HELPERS
# =========================


def create_initial_context() -> AirlineAgentContext:
    """Factory for a new AirlineAgentContext."""

    ctx = AirlineAgentContext()
    ctx.account_number = str(random.randint(10000000, 99999999))
    return ctx


def _context_snapshot(context: AirlineAgentContext) -> str:
    data = context.model_dump(exclude_none=True)
    if not data:
        return "No known context yet."
    parts = [f"{key.replace('_', ' ').title()}: {value}" for key, value in data.items()]
    return " | ".join(parts)


def _format_history(history: List[Dict[str, Any]], limit: int = 6) -> str:
    """Return the last few turns as plain text for the LLM."""

    tail = history[-limit:]
    formatted = []
    for message in tail:
        role = message.get("role", "user").title()
        agent = message.get("agent")
        prefix = f"{role}"
        if agent:
            prefix += f" ({agent})"
        formatted.append(f"{prefix}: {message.get('content', '')}")
    return "\n".join(formatted) if formatted else "No prior conversation."


def _extract_json_block(text: str) -> Dict[str, Any]:
    """Attempt to parse a JSON object embedded in the model output."""

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            snippet = text[start : end + 1]
            try:
                return json.loads(snippet)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Unable to parse JSON from response: {text}") from exc
        raise ValueError(f"Unable to parse JSON from response: {text}")


# =========================
# GUARDRAILS
# =========================


async def _run_guardrail(
    *,
    name: str,
    message: str,
    schema_description: str,
) -> GuardrailDecision:
    system_prompt = (
        "You are a classification guardrail for an airline customer service assistant. "
        "Read the latest user message and respond with strict JSON following this schema: "
        f"{schema_description}"
    )
    user_prompt = json.dumps({"message": message})
    data = await chat(
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        temperature=0.0,
        top_p=0.1,
        max_tokens=200,
    )
    content = extract_text_choice(data)
    parsed = _extract_json_block(content)

    if name == "Relevance Guardrail":
        is_relevant = bool(parsed.get("is_relevant"))
        reasoning = str(parsed.get("reasoning", ""))
        return GuardrailDecision(name=name, passed=is_relevant, reasoning=reasoning)
    if name == "Jailbreak Guardrail":
        is_safe = bool(parsed.get("is_safe"))
        reasoning = str(parsed.get("reasoning", ""))
        return GuardrailDecision(name=name, passed=is_safe, reasoning=reasoning)
    raise ValueError(f"Unknown guardrail: {name}")


async def run_relevance_guardrail(message: str) -> GuardrailDecision:
    schema = '{"is_relevant": <bool>, "reasoning": "<short explanation>"}'
    return await _run_guardrail(name="Relevance Guardrail", message=message, schema_description=schema)


async def run_jailbreak_guardrail(message: str) -> GuardrailDecision:
    schema = '{"is_safe": <bool>, "reasoning": "<short explanation>"}'
    return await _run_guardrail(name="Jailbreak Guardrail", message=message, schema_description=schema)


# =========================
# TOOLS
# =========================


async def faq_lookup_tool(question: str) -> str:
    q = question.lower()
    if "bag" in q or "baggage" in q:
        return (
            "You are allowed to bring one bag on the plane. "
            "It must be under 50 pounds and 22 inches x 14 inches x 9 inches."
        )
    if "seats" in q or "plane" in q:
        return (
            "There are 120 seats on the plane. "
            "There are 22 business class seats and 98 economy seats. "
            "Exit rows are rows 4 and 16. Rows 5-8 are Economy Plus, with extra legroom."
        )
    if "wifi" in q:
        return "We have free wifi on the plane, join Airline-Wifi"
    return "I'm sorry, I don't know the answer to that question."


async def update_seat(context: AirlineAgentContext, confirmation_number: str, new_seat: str) -> str:
    context.confirmation_number = confirmation_number
    context.seat_number = new_seat
    if context.flight_number is None:
        context.flight_number = f"FLT-{random.randint(100, 999)}"
    return f"Updated seat to {new_seat} for confirmation number {confirmation_number}"


async def flight_status_tool(flight_number: str) -> str:
    return f"Flight {flight_number} is on time and scheduled to depart at gate A10."


async def baggage_tool(query: str) -> str:
    q = query.lower()
    if "fee" in q:
        return "Overweight bag fee is $75."
    if "allowance" in q:
        return "One carry-on and one checked bag (up to 50 lbs) are included."
    return "Please provide details about your baggage inquiry."


async def display_seat_map() -> str:
    return "DISPLAY_SEAT_MAP"


async def cancel_flight(context: AirlineAgentContext) -> str:
    if context.flight_number is None:
        raise ValueError("Flight number is required")
    return f"Flight {context.flight_number} successfully cancelled"


TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {
    "faq_lookup_tool": {"callable": faq_lookup_tool, "pass_context": False},
    "baggage_tool": {"callable": baggage_tool, "pass_context": False},
    "update_seat": {"callable": update_seat, "pass_context": True},
    "display_seat_map": {"callable": display_seat_map, "pass_context": False},
    "flight_status_tool": {"callable": flight_status_tool, "pass_context": False},
    "cancel_flight": {"callable": cancel_flight, "pass_context": True},
}


# =========================
# AGENT IMPLEMENTATION
# =========================


class LlmAgent:
    """High-level agent powered by a Perplexity chat completion."""

    def __init__(
        self,
        *,
        name: str,
        description: str,
        instructions_builder,
        available_tools: Optional[List[str]] = None,
        handoffs: Optional[List[str]] = None,
        default_model: str = "sonar",
    ) -> None:
        self.name = name
        self.description = description
        self._instructions_builder = instructions_builder
        self.available_tools = available_tools or []
        self.handoffs = handoffs or []
        self.default_model = default_model

    async def run(
        self,
        *,
        state: ConversationState,
        user_message: str,
    ) -> AgentRunResult:
        context = state.context
        history_text = _format_history(state.history)
        instructions = self._instructions_builder(context)
        tool_names = list(self.available_tools)
        schema_description = (
            "Return a strict JSON object with keys: "
            "`messages` (array of strings for the customer), optional `tool_call` (object with `name` and `arguments`), "
            "and optional `handoff` containing the exact name of another agent to transfer to. "
            "Example: {""messages"": [""text""], ""tool_call"": {""name"": ""update_seat"", ""arguments"": {""new_seat"": ""23A""}}}"
        )

        user_payload = json.dumps(
            {
                "conversation_history": history_text,
                "user_message": user_message,
                "toolbox": tool_names,
                "context": context.model_dump(),
            }
        )

        data = await chat(
            messages=[
                {"role": "system", "content": instructions + "\n" + schema_description},
                {"role": "user", "content": user_payload},
            ],
            model=self.default_model,
            temperature=0.2,
            top_p=0.9,
        )
        content = extract_text_choice(data)
        parsed = _extract_json_block(content)

        messages = parsed.get("messages") or []
        if not isinstance(messages, list):
            messages = [str(messages)]
        messages = [str(m) for m in messages]

        handoff = parsed.get("handoff")
        if handoff is not None:
            handoff = str(handoff)

        tool_calls: List[ToolInvocation] = []
        tool_payload = parsed.get("tool_call")
        if tool_payload and isinstance(tool_payload, dict):
            tool_name = tool_payload.get("name")
            arguments = tool_payload.get("arguments", {})
            if tool_name in self.available_tools:
                tool_calls.append(
                    ToolInvocation(name=str(tool_name), arguments=dict(arguments))
                )

        return AgentRunResult(messages=messages, handoff=handoff, tool_calls=tool_calls)


def _ensure_confirmation(context: AirlineAgentContext) -> None:
    if context.confirmation_number is None:
        context.confirmation_number = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


def _ensure_flight_number(context: AirlineAgentContext) -> None:
    if context.flight_number is None:
        context.flight_number = f"FLT-{random.randint(100, 999)}"


def _seat_booking_instructions(context: AirlineAgentContext) -> str:
    _ensure_confirmation(context)
    _ensure_flight_number(context)
    return (
        "You are the Seat Booking Agent for Airline Co. Help customers change seats. "
        f"Known context: {_context_snapshot(context)}. "
        "Ask for missing confirmation or seat details before updating. "
        "If the customer wants to change seats, gather the desired seat number and call the `update_seat` tool with both the confirmation number and the new seat. "
        "If they want to browse seats, you may call the `display_seat_map` tool."
    )


def _faq_instructions(context: AirlineAgentContext) -> str:
    return (
        "You are the FAQ Agent. Answer airline policy questions with the provided tools only. "
        f"Known context: {_context_snapshot(context)}. "
        "Use `faq_lookup_tool` when you need factual information."
    )


def _flight_status_instructions(context: AirlineAgentContext) -> str:
    _ensure_confirmation(context)
    _ensure_flight_number(context)
    return (
        "You are the Flight Status Agent. Provide precise status updates. "
        f"Known context: {_context_snapshot(context)}. "
        "Gather missing confirmation or flight numbers before responding and call `flight_status_tool` once you have the flight number."
    )


def _cancellation_instructions(context: AirlineAgentContext) -> str:
    _ensure_confirmation(context)
    _ensure_flight_number(context)
    return (
        "You are the Cancellation Agent. Verify customer confirmation before cancelling. "
        f"Known context: {_context_snapshot(context)}. "
        "Confirm the flight details and call `cancel_flight` when the customer agrees to cancel."
    )


def _triage_instructions(context: AirlineAgentContext) -> str:
    return (
        "You are the Triage Agent. Decide which specialist should handle the customer's latest request. "
        "Select from: Seat Booking Agent, Flight Status Agent, Cancellation Agent, FAQ Agent. "
        "Explain your reasoning. Respond only with JSON {\"agent\": <name>, \"reason\": <short>}."
    )


TRIAGE_AGENT = LlmAgent(
    name="Triage Agent",
    description="Routes the customer's request to the appropriate specialist agent.",
    instructions_builder=_triage_instructions,
)

SEAT_BOOKING_AGENT = LlmAgent(
    name="Seat Booking Agent",
    description="Helps customers change seats and trigger seat map displays.",
    instructions_builder=_seat_booking_instructions,
    available_tools=["update_seat", "display_seat_map"],
    handoffs=["Triage Agent"],
)

FAQ_AGENT = LlmAgent(
    name="FAQ Agent",
    description="Answers airline FAQs via the faq lookup tool.",
    instructions_builder=_faq_instructions,
    available_tools=["faq_lookup_tool", "baggage_tool"],
    handoffs=["Triage Agent"],
)

FLIGHT_STATUS_AGENT = LlmAgent(
    name="Flight Status Agent",
    description="Shares flight status updates.",
    instructions_builder=_flight_status_instructions,
    available_tools=["flight_status_tool"],
    handoffs=["Triage Agent"],
)

CANCELLATION_AGENT = LlmAgent(
    name="Cancellation Agent",
    description="Cancels flights after customer confirmation.",
    instructions_builder=_cancellation_instructions,
    available_tools=["cancel_flight"],
    handoffs=["Triage Agent"],
)

AGENT_REGISTRY: Dict[str, LlmAgent] = {
    agent.name: agent
    for agent in [
        TRIAGE_AGENT,
        SEAT_BOOKING_AGENT,
        FAQ_AGENT,
        FLIGHT_STATUS_AGENT,
        CANCELLATION_AGENT,
    ]
}


async def run_triage(state: ConversationState, user_message: str) -> Tuple[str, str]:
    data = await chat(
        messages=[
            {
                "role": "system",
                "content": _triage_instructions(state.context)
                + " You must respond with JSON {\"agent\": <name>, \"reason\": <short note>}.",
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "conversation_history": _format_history(state.history),
                        "user_message": user_message,
                        "available_agents": [
                            {"name": agent.name, "description": agent.description}
                            for agent in AGENT_REGISTRY.values()
                            if agent.name != "Triage Agent"
                        ],
                    }
                ),
            },
        ],
        temperature=0.0,
        top_p=0.1,
    )
    content = extract_text_choice(data)
    parsed = _extract_json_block(content)
    agent_name = str(parsed.get("agent", "FAQ Agent"))
    reason = str(parsed.get("reason", ""))
    if agent_name not in AGENT_REGISTRY or agent_name == "Triage Agent":
        agent_name = "FAQ Agent"
    return agent_name, reason


async def run_agent(
    *,
    agent_name: str,
    state: ConversationState,
    user_message: str,
) -> AgentRunResult:
    agent = AGENT_REGISTRY[agent_name]
    return await agent.run(state=state, user_message=user_message)


def list_agents() -> List[Dict[str, Any]]:
    items = []
    for agent in AGENT_REGISTRY.values():
        items.append(
            {
                "name": agent.name,
                "description": agent.description,
                "handoffs": agent.handoffs,
                "tools": list(agent.available_tools),
                "input_guardrails": ["Relevance Guardrail", "Jailbreak Guardrail"],
            }
        )
    return items
