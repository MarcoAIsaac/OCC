from __future__ import annotations

import pytest

from occ.ai_assistant import AssistantError, _extract_openai_output_text, ask_openai


def test_extract_openai_output_text_prefers_top_level_field() -> None:
    payload = {"output_text": "  ready text  "}
    assert _extract_openai_output_text(payload) == "ready text"


def test_extract_openai_output_text_falls_back_to_output_blocks() -> None:
    payload = {
        "output": [
            {
                "content": [
                    {"type": "output_text", "text": "first"},
                    {"type": "output_text", "output_text": "second"},
                ]
            }
        ]
    }
    assert _extract_openai_output_text(payload) == "first\n\nsecond"


def test_ask_openai_requires_api_key() -> None:
    with pytest.raises(AssistantError):
        ask_openai(prompt="hello", model="gpt-4.1-mini", api_key="")
