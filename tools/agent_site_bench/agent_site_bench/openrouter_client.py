from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import httpx


def load_openrouter_api_key() -> str | None:
    try:
        from dotenv import find_dotenv, load_dotenv

        dotenv_path = find_dotenv(usecwd=True)
        if dotenv_path:
            load_dotenv(dotenv_path)
    except Exception:
        # Environment variables still work if python-dotenv is not importable.
        pass

    if os.environ.get("OPENROUTER_API_KEY"):
        return os.environ["OPENROUTER_API_KEY"]

    # A tiny fallback for cases where python-dotenv is unavailable.
    for parent in [Path.cwd(), *Path.cwd().parents]:
        dotenv = parent / ".env"
        if not dotenv.exists():
            continue
        for line in dotenv.read_text(encoding="utf-8", errors="ignore").splitlines():
            if not line.startswith("OPENROUTER_API_KEY="):
                continue
            value = line.split("=", 1)[1].strip().strip('"').strip("'")
            return value or None
    return None


class OpenRouterClient:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = "https://openrouter.ai/api/v1",
        timeout_seconds: float = 60.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(
            timeout=timeout_seconds,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/julianhernandez2155/su-kb-site",
                "X-Title": "agent_site_bench",
            },
        )

    def close(self) -> None:
        self.client.close()

    def chat_completion(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        response_format: dict[str, Any] | None = None,
        temperature: float = 0,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if tools is not None:
            payload["tools"] = tools
        if tool_choice is not None:
            payload["tool_choice"] = tool_choice
        if response_format is not None:
            payload["response_format"] = response_format

        response = self.client.post(f"{self.base_url}/chat/completions", json=payload)
        if response.status_code >= 400:
            raise RuntimeError(f"OpenRouter error {response.status_code}: {response.text[:1000]}")
        return response.json()
