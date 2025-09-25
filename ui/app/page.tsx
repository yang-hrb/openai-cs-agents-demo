"use client";

import { useCallback, useEffect, useState } from "react";
import { AgentPanel } from "@/components/agent-panel";
import { Chat } from "@/components/chat";
import type { Agent, AgentEvent, GuardrailCheck, Message } from "@/lib/types";
import { callChatAPI } from "@/lib/api";

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [currentAgent, setCurrentAgent] = useState<string>("");
  const [guardrails, setGuardrails] = useState<GuardrailCheck[]>([]);
  const [context, setContext] = useState<Record<string, any>>({});
  const [conversationId, setConversationId] = useState<string | null>(null);
  // Loading state while awaiting assistant response
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const appendAssistantMessage = useCallback((content: string, agent?: string) => {
    setMessages((prev) => [
      ...prev,
      {
        id: Date.now().toString() + Math.random().toString(),
        content,
        role: "assistant",
        agent,
        timestamp: new Date(),
      },
    ]);
  }, []);

  const bootConversation = useCallback(async () => {
    const result = await callChatAPI("", "");

    if (!result.ok) {
      setErrorMessage(result.error);
      appendAssistantMessage(result.error);
      return;
    }

    const data = result.data;
    setErrorMessage(null);
    setConversationId(data.conversation_id);
    setCurrentAgent(data.current_agent);
    setContext(data.context);
    const initialEvents = (data.events || []).map((e: any) => ({
      ...e,
      timestamp: e.timestamp ?? Date.now(),
    }));
    setEvents(initialEvents);
    setAgents(data.agents || []);
    setGuardrails(data.guardrails || []);
    if (Array.isArray(data.messages)) {
      setMessages(
        data.messages.map((m: any) => ({
          id: Date.now().toString() + Math.random().toString(),
          content: m.content,
          role: "assistant",
          agent: m.agent,
          timestamp: new Date(),
        }))
      );
    }
  }, [appendAssistantMessage]);

  // Boot the conversation
  useEffect(() => {
    void bootConversation();
  }, [bootConversation]);

  // Send a user message
  const handleSendMessage = async (content: string) => {
    const userMsg: Message = {
      id: Date.now().toString(),
      content,
      role: "user",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    const result = await callChatAPI(content, conversationId ?? "");

    if (!result.ok) {
      setErrorMessage(result.error);
      appendAssistantMessage(result.error);
      setIsLoading(false);
      return;
    }

    const data = result.data;
    setErrorMessage(null);
    if (!conversationId) setConversationId(data.conversation_id);
    setCurrentAgent(data.current_agent);
    setContext(data.context);
    if (data.events) {
      const stamped = data.events.map((e: any) => ({
        ...e,
        timestamp: e.timestamp ?? Date.now(),
      }));
      setEvents((prev) => [...prev, ...stamped]);
    }
    if (data.agents) setAgents(data.agents);
    if (data.guardrails) setGuardrails(data.guardrails);

    if (data.messages) {
      const responses: Message[] = data.messages.map((m: any) => ({
        id: Date.now().toString() + Math.random().toString(),
        content: m.content,
        role: "assistant",
        agent: m.agent,
        timestamp: new Date(),
      }));
      setMessages((prev) => [...prev, ...responses]);
    }

    setIsLoading(false);
  };

  return (
    <main className="flex h-screen gap-2 bg-gray-100 p-2">
      {errorMessage && (
        <div className="absolute left-4 right-4 top-4 z-10 rounded-lg border border-red-300 bg-red-50 px-4 py-2 text-sm text-red-800 shadow-sm">
          {errorMessage}
        </div>
      )}
      <AgentPanel
        agents={agents}
        currentAgent={currentAgent}
        events={events}
        guardrails={guardrails}
        context={context}
      />
      <Chat
        messages={messages}
        onSendMessage={handleSendMessage}
        isLoading={isLoading}
      />
    </main>
  );
}
