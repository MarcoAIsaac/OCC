from __future__ import annotations

from occ.offline_assistant import ask_offline


def test_offline_assistant_mentions_lab_for_matrix_prompt() -> None:
    reply = ask_offline("How can I compare claims in a matrix?")
    assert "occ lab run" in reply


def test_offline_assistant_handles_no_eval_context() -> None:
    reply = ask_offline("help", context="latest verdict NO-EVAL(L4C6)")
    assert "NO-EVAL" in reply
