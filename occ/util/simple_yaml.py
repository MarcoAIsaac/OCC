"""Tiny YAML loader fallback used when PyYAML is unavailable.

This parser intentionally supports a conservative YAML subset that covers the
OCC repository configuration files:

- mappings with indentation
- lists using ``-`` entries
- quoted or plain scalars
- booleans/null/numbers
- folded blocks using ``>-``

It is **not** a full YAML implementation.
"""

from __future__ import annotations

import ast
from typing import Any, List, Tuple


class _Line:
    def __init__(self, indent: int, text: str) -> None:
        self.indent = indent
        self.text = text


def _strip_comment(raw: str) -> str:
    in_single = False
    in_double = False
    out: List[str] = []
    for ch in raw:
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == "#" and not in_single and not in_double:
            break
        out.append(ch)
    return "".join(out).rstrip()


def _tokenize(text: str) -> List[_Line]:
    lines: List[_Line] = []
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        cleaned = _strip_comment(raw[indent:])
        if not cleaned:
            continue
        lines.append(_Line(indent, cleaned))
    return lines


def _parse_scalar(value: str) -> Any:
    if not value:
        return ""
    low = value.lower()
    if low in {"true", "yes"}:
        return True
    if low in {"false", "no"}:
        return False
    if low in {"null", "none", "~"}:
        return None
    if value[0] in {"'", '"'} and value[-1] == value[0]:
        return ast.literal_eval(value)
    if value[0] in "-0123456789":
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            pass
    return value


def _split_keyval(text: str) -> Tuple[str, str | None]:
    in_single = False
    in_double = False
    for i, ch in enumerate(text):
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == ":" and not in_single and not in_double:
            key = text[:i].strip()
            rest = text[i + 1 :].strip()
            return key, (rest if rest else None)
    raise ValueError(f"Invalid YAML mapping entry: {text!r}")


def _parse_block(lines: List[_Line], idx: int, indent: int) -> Tuple[Any, int]:
    if idx >= len(lines):
        return {}, idx

    if lines[idx].indent < indent:
        return {}, idx

    is_list = lines[idx].text.startswith("-") and lines[idx].indent == indent
    out: Any = [] if is_list else {}

    while idx < len(lines):
        line = lines[idx]
        if line.indent < indent:
            break
        if is_list:
            if line.indent != indent or not line.text.startswith("-"):
                break
            payload = line.text[1:].strip()
            idx += 1
            if not payload:
                value, idx = _parse_block(lines, idx, indent + 2)
                out.append(value)
                continue
            if ":" in payload and not payload.startswith(('"', "'")):
                key, val = _split_keyval(payload)
                item: dict[str, Any] = {}
                if val is None:
                    nested, idx = _parse_block(lines, idx, indent + 2)
                    item[key] = nested
                elif val == ">-":
                    folded: List[str] = []
                    while idx < len(lines) and lines[idx].indent > indent:
                        folded.append(lines[idx].text.strip())
                        idx += 1
                    item[key] = " ".join(folded)
                else:
                    item[key] = _parse_scalar(val)
                while idx < len(lines) and lines[idx].indent >= indent + 2:
                    nline = lines[idx]
                    if nline.indent != indent + 2 or nline.text.startswith("-"):
                        break
                    nkey, nval = _split_keyval(nline.text)
                    idx += 1
                    if nval is None:
                        nested, idx = _parse_block(lines, idx, indent + 4)
                        item[nkey] = nested
                    elif nval == ">-":
                        folded = []
                        while idx < len(lines) and lines[idx].indent > indent + 2:
                            folded.append(lines[idx].text.strip())
                            idx += 1
                        item[nkey] = " ".join(folded)
                    else:
                        item[nkey] = _parse_scalar(nval)
                out.append(item)
            else:
                out.append(_parse_scalar(payload))
        else:
            if line.indent != indent:
                break
            key, val = _split_keyval(line.text)
            idx += 1
            if val is None:
                nested, idx = _parse_block(lines, idx, indent + 2)
                out[key] = nested
            elif val == ">-":
                folded_root: List[str] = []
                while idx < len(lines) and lines[idx].indent > indent:
                    folded_root.append(lines[idx].text.strip())
                    idx += 1
                out[key] = " ".join(folded_root)
            else:
                out[key] = _parse_scalar(val)

    return out, idx


def safe_load(text: str) -> Any:
    lines = _tokenize(text)
    if not lines:
        return None
    data, _ = _parse_block(lines, 0, lines[0].indent)
    return data
