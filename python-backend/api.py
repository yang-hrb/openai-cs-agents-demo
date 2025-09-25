import asyncio
import logging
import time
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from main import (
    AGENT_REGISTRY,
    ConversationState,
    GuardrailDecision,
    ToolInvocation,
    create_initial_context,
    list_agents,
    run_agent,
    run_jailbreak_guardrail,
    run_relevance_guardrail,
    run_triage,
    TOOL_REGISTRY,
)
from perplexity_client import PerplexityError

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str


class MessageResponse(BaseModel):
    content: str
    agent: str


class AgentEvent(BaseModel):
    id: str
    type: str
    agent: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    timestamp: float


class GuardrailCheck(BaseModel):
    id: str
    name: str
    input: str
    reasoning: str
    passed: bool
    timestamp: float


class ChatResponse(BaseModel):
    conversation_id: str
    current_agent: str
    messages: List[MessageResponse]
    events: List[AgentEvent]
    context: Dict[str, Any]
    agents: List[Dict[str, Any]]
    guardrails: List[GuardrailCheck]


class ConversationStore:
    def get(self, conversation_id: str) -> Optional[ConversationState]:
        raise NotImplementedError

    def save(self, conversation_id: str, state: ConversationState) -> None:
        raise NotImplementedError


class InMemoryConversationStore(ConversationStore):
    _store: Dict[str, ConversationState] = {}

    def get(self, conversation_id: str) -> Optional[ConversationState]:
        return self._store.get(conversation_id)

    def save(self, conversation_id: str, state: ConversationState) -> None:
        self._store[conversation_id] = state


conversation_store = InMemoryConversationStore()


async def _evaluate_guardrails(message: str) -> List[GuardrailDecision]:
    relevance, jailbreak = await asyncio.gather(
        run_relevance_guardrail(message),
        run_jailbreak_guardrail(message),
    )
    return [relevance, jailbreak]


async def _execute_tool(invocation: ToolInvocation, state: ConversationState) -> str:
    tool_info = TOOL_REGISTRY.get(invocation.name)
    if not tool_info:
        raise ValueError(f"Unknown tool requested: {invocation.name}")
    func = tool_info["callable"]
    args = invocation.arguments or {}
    if tool_info.get("pass_context"):
        return await func(state.context, **args)
    return await func(**args)


def _build_guardrail_checks(message: str, decisions: List[GuardrailDecision]) -> List[GuardrailCheck]:
    timestamp = time.time() * 1000
    return [
        GuardrailCheck(
            id=uuid4().hex,
            name=decision.name,
            input=message,
            reasoning=decision.reasoning,
            passed=decision.passed,
            timestamp=timestamp,
        )
        for decision in decisions
    ]


def _context_changes(before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Any]:
    return {key: after[key] for key in after if before.get(key) != after[key]}


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest) -> ChatResponse:  # noqa: C901 - endpoint orchestration
    is_new = not req.conversation_id or conversation_store.get(req.conversation_id) is None
    if is_new:
        conversation_id = uuid4().hex
        state = ConversationState(context=create_initial_context())
        conversation_store.save(conversation_id, state)
    else:
        conversation_id = req.conversation_id  # type: ignore[assignment]
        state = conversation_store.get(conversation_id)
        if state is None:
            raise HTTPException(status_code=404, detail="Conversation not found")

    message_text = req.message.strip()
    if message_text == "":
        return ChatResponse(
            conversation_id=conversation_id,
            current_agent=state.current_agent,
            messages=[],
            events=[],
            context=state.context.model_dump(),
            agents=list_agents(),
            guardrails=[],
        )

    state.history.append({"role": "user", "content": message_text})

    try:
        guardrail_decisions = await _evaluate_guardrails(message_text)
    except PerplexityError as exc:
        logger.exception("Guardrail evaluation failed")
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    guardrail_checks = _build_guardrail_checks(message_text, guardrail_decisions)
    if any(not decision.passed for decision in guardrail_decisions):
        refusal = "Sorry, I can only answer questions related to airline travel."
        state.history.append({"role": "assistant", "agent": state.current_agent, "content": refusal})
        conversation_store.save(conversation_id, state)
        return ChatResponse(
            conversation_id=conversation_id,
            current_agent=state.current_agent,
            messages=[MessageResponse(content=refusal, agent=state.current_agent)],
            events=[],
            context=state.context.model_dump(),
            agents=list_agents(),
            guardrails=guardrail_checks,
        )

    try:
        target_agent, routing_reason = await run_triage(state, message_text)
        agent_result = await run_agent(agent_name=target_agent, state=state, user_message=message_text)
    except PerplexityError as exc:
        logger.exception("Perplexity request failed")
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    events: List[AgentEvent] = []
    messages: List[MessageResponse] = []

    previous_agent = state.current_agent
    if previous_agent != target_agent:
        events.append(
            AgentEvent(
                id=uuid4().hex,
                type="handoff",
                agent=previous_agent,
                content=f"{previous_agent} -> {target_agent}",
                metadata={
                    "source_agent": previous_agent,
                    "target_agent": target_agent,
                    "reason": routing_reason,
                },
                timestamp=time.time() * 1000,
            )
        )
    state.current_agent = target_agent

    for invocation in agent_result.tool_calls:
        before = state.context.model_dump()
        try:
            result = await _execute_tool(invocation, state)
        except Exception as error:  # noqa: BLE001
            logger.exception("Tool execution failed")
            result = f"Tool {invocation.name} failed: {error}"
        invocation.result = result
        events.append(
            AgentEvent(
                id=uuid4().hex,
                type="tool_call",
                agent=target_agent,
                content=invocation.name,
                metadata={"tool_args": invocation.arguments},
                timestamp=time.time() * 1000,
            )
        )
        events.append(
            AgentEvent(
                id=uuid4().hex,
                type="tool_output",
                agent=target_agent,
                content=str(result),
                metadata={"tool_result": result},
                timestamp=time.time() * 1000,
            )
        )
        if isinstance(result, str) and result.strip().upper() == "DISPLAY_SEAT_MAP":
            state.history.append({"role": "assistant", "agent": target_agent, "content": "DISPLAY_SEAT_MAP"})
            messages.append(MessageResponse(content="DISPLAY_SEAT_MAP", agent=target_agent))
            events.append(
                AgentEvent(
                    id=uuid4().hex,
                    type="message",
                    agent=target_agent,
                    content="DISPLAY_SEAT_MAP",
                    timestamp=time.time() * 1000,
                )
            )
        after = state.context.model_dump()
        changes = _context_changes(before, after)
        if changes:
            events.append(
                AgentEvent(
                    id=uuid4().hex,
                    type="context_update",
                    agent=target_agent,
                    content="",
                    metadata={"changes": changes},
                    timestamp=time.time() * 1000,
                )
            )

    for line in agent_result.messages:
        state.history.append({"role": "assistant", "agent": target_agent, "content": line})
        timestamp = time.time() * 1000
        messages.append(MessageResponse(content=line, agent=target_agent))
        events.append(
            AgentEvent(
                id=uuid4().hex,
                type="message",
                agent=target_agent,
                content=line,
                timestamp=timestamp,
            )
        )

    if agent_result.handoff and agent_result.handoff in AGENT_REGISTRY:
        next_agent = agent_result.handoff
        events.append(
            AgentEvent(
                id=uuid4().hex,
                type="handoff",
                agent=target_agent,
                content=f"{target_agent} -> {next_agent}",
                metadata={"source_agent": target_agent, "target_agent": next_agent},
                timestamp=time.time() * 1000,
            )
        )
        state.current_agent = next_agent

    conversation_store.save(conversation_id, state)

    return ChatResponse(
        conversation_id=conversation_id,
        current_agent=state.current_agent,
        messages=messages,
        events=events,
        context=state.context.model_dump(),
        agents=list_agents(),
        guardrails=guardrail_checks,
    )
