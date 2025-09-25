import os
from typing import Any, Dict, List, Optional

import httpx

API_URL = "https://api.perplexity.ai/chat/completions"
DEFAULT_MODEL = os.getenv("PPLX_MODEL", "sonar")
_TIMEOUT = httpx.Timeout(30.0, read=60.0)


class PerplexityError(RuntimeError):
    """Raised when the Perplexity API reports an error."""


async def chat(
    messages: List[Dict[str, str]],
    *,
    model: Optional[str] = None,
    temperature: float = 0.2,
    top_p: float = 0.9,
    max_tokens: Optional[int] = None,
) -> Dict[str, Any]:
    """Call the Perplexity chat completion endpoint and return the parsed body."""
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        raise PerplexityError("PERPLEXITY_API_KEY environment variable is not set")

    payload: Dict[str, Any] = {
        "model": model or DEFAULT_MODEL,
        "messages": messages,
        "temperature": temperature,
        "top_p": top_p,
    }
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        response = await client.post(API_URL, json=payload, headers=headers)
    if response.status_code >= 400:
        raise PerplexityError(f"Perplexity API error: {response.status_code} {response.text}")

    data = response.json()
    if "choices" not in data or not data["choices"]:
        raise PerplexityError("Unexpected Perplexity API response: missing choices")

    return data


def extract_text_choice(data: Dict[str, Any]) -> str:
    """Helper to extract the first message content string from a chat response."""
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, TypeError) as exc:
        raise PerplexityError("Malformed Perplexity response payload") from exc
