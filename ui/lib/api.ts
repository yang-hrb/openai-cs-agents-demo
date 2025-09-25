export type ChatAPISuccess<TData = any> = { ok: true; data: TData }
export type ChatAPIError = { ok: false; error: string }
export type ChatAPIResult<TData = any> = ChatAPISuccess<TData> | ChatAPIError

function normaliseError(value: unknown, fallback: string): string {
  if (value instanceof Error && value.message) return value.message
  if (typeof value === "string" && value.trim()) return value
  return fallback
}

// Helper to call the server and surface failures to the UI
export async function callChatAPI(message: string, conversationId: string): Promise<ChatAPIResult> {
  try {
    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ conversation_id: conversationId, message }),
    })

    if (!res.ok) {
      let detail = `Chat API error: ${res.status}`
      try {
        const body = await res.json()
        if (body?.detail) detail = String(body.detail)
      } catch (parseErr) {
        console.error("Failed to parse error response:", parseErr)
      }
      return { ok: false, error: detail }
    }

    const data = await res.json()
    return { ok: true, data }
  } catch (err) {
    console.error("Error sending message:", err)
    return { ok: false, error: normaliseError(err, "Unable to reach chat service.") }
  }
}
