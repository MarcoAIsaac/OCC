"""AI assistant integration for OCC Desktop.

This module intentionally uses standard-library HTTP so the desktop app can
ship without extra runtime dependencies.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"

DEFAULT_SYSTEM_PROMPT = (
    "You are the OCC Desktop assistant. Be concise, practical, and aligned with "
    "the OCC runtime, judges/locks, and reproducible workflow constraints."
)


class AssistantError(RuntimeError):
    """Raised when the assistant backend request fails."""


def _extract_openai_output_text(payload: Dict[str, Any]) -> str:
    if isinstance(payload.get("output_text"), str) and payload["output_text"].strip():
        return str(payload["output_text"]).strip()

    outputs = payload.get("output")
    parts: List[str] = []
    if isinstance(outputs, list):
        for item in outputs:
            if not isinstance(item, dict):
                continue
            content = item.get("content")
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict):
                    continue
                if isinstance(block.get("text"), str) and block["text"].strip():
                    parts.append(block["text"].strip())
                elif isinstance(block.get("output_text"), str) and block["output_text"].strip():
                    parts.append(block["output_text"].strip())

    text = "\n\n".join(x for x in parts if x)
    if text:
        return text
    raise AssistantError("No assistant text found in OpenAI response payload.")


def _http_json_post(
    url: str,
    headers: Dict[str, str],
    body: Dict[str, Any],
    timeout_s: int,
) -> Dict[str, Any]:
    request = urllib.request.Request(
        url=url,
        data=json.dumps(body).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        raw_error = e.read().decode("utf-8", errors="replace")
        message = raw_error
        try:
            decoded = json.loads(raw_error)
            if isinstance(decoded, dict):
                err = decoded.get("error")
                if isinstance(err, dict) and isinstance(err.get("message"), str):
                    message = err["message"]
        except json.JSONDecodeError:
            pass
        raise AssistantError(f"HTTP {e.code}: {message}") from e
    except urllib.error.URLError as e:
        raise AssistantError(f"Connection error: {e}") from e

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise AssistantError("Invalid JSON response from assistant provider.") from e
    if not isinstance(data, dict):
        raise AssistantError("Unexpected assistant response shape.")
    return data


def ask_openai(
    prompt: str,
    model: str,
    api_key: Optional[str] = None,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    timeout_s: int = 45,
) -> str:
    key = (api_key or os.getenv("OPENAI_API_KEY") or "").strip()
    if not key:
        raise AssistantError("Missing OPENAI_API_KEY.")

    user_prompt = prompt.strip()
    if not user_prompt:
        raise AssistantError("Prompt is empty.")

    request_payload: Dict[str, Any] = {
        "model": model.strip() or "gpt-4.1-mini",
        "input": [],
    }
    if system_prompt.strip():
        request_payload["input"].append(
            {
                "role": "system",
                "content": [{"type": "input_text", "text": system_prompt.strip()}],
            }
        )
    request_payload["input"].append(
        {
            "role": "user",
            "content": [{"type": "input_text", "text": user_prompt}],
        }
    )

    response_json = _http_json_post(
        OPENAI_RESPONSES_URL,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        body=request_payload,
        timeout_s=timeout_s,
    )
    return _extract_openai_output_text(response_json)
