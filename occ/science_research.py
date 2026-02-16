"""Lightweight scientific web research helpers.

This module intentionally uses only stdlib networking/parsing so OCC can run in
minimal environments.
"""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping

USER_AGENT = "occ-mrd-runner/1.1 (+https://github.com/MarcoAIsaac/OCC)"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_text(url: str, timeout_s: int) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        raw = resp.read()
    if isinstance(raw, bytes):
        return raw.decode("utf-8", errors="replace")
    return str(raw)


def _get_json(url: str, timeout_s: int) -> Dict[str, Any]:
    obj = json.loads(_get_text(url, timeout_s=timeout_s))
    if isinstance(obj, dict):
        return obj
    return {}


def _tokens(text: str) -> List[str]:
    return re.findall(r"[A-Za-z0-9_+\-]{3,}", text)


def build_query_from_claim(claim: Mapping[str, Any]) -> str:
    raw_parts: List[str] = []

    title = claim.get("title")
    if isinstance(title, str):
        raw_parts.append(title)

    domain = claim.get("domain")
    if isinstance(domain, Mapping):
        omega = domain.get("omega_I")
        if isinstance(omega, str):
            raw_parts.append(omega)
        observables = domain.get("observables")
        if isinstance(observables, list):
            raw_parts.extend(str(x) for x in observables)

    params = claim.get("parameters")
    if isinstance(params, list):
        for p in params:
            if isinstance(p, Mapping):
                name = p.get("name")
                if isinstance(name, str):
                    raw_parts.append(name)

    keywords: List[str] = []
    seen: set[str] = set()
    for part in raw_parts:
        for t in _tokens(part):
            low = t.lower()
            if low in seen:
                continue
            seen.add(low)
            keywords.append(t)
            if len(keywords) >= 12:
                break
        if len(keywords) >= 12:
            break

    if keywords:
        return " ".join(keywords)
    return "operational consistency falsifiable prediction"


def search_arxiv(query: str, max_results: int = 5, timeout_s: int = 15) -> List[Dict[str, Any]]:
    params = urllib.parse.urlencode(
        {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": max_results,
            "sortBy": "relevance",
            "sortOrder": "descending",
        }
    )
    url = f"https://export.arxiv.org/api/query?{params}"
    xml_text = _get_text(url, timeout_s=timeout_s)

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(xml_text)
    out: List[Dict[str, Any]] = []
    for entry in root.findall("atom:entry", ns):
        title = " ".join((entry.findtext("atom:title", default="", namespaces=ns)).split())
        summary = " ".join((entry.findtext("atom:summary", default="", namespaces=ns)).split())
        link = entry.findtext("atom:id", default="", namespaces=ns)
        published = entry.findtext("atom:published", default="", namespaces=ns)

        authors: List[str] = []
        for author in entry.findall("atom:author", ns):
            a = author.findtext("atom:name", default="", namespaces=ns).strip()
            if a:
                authors.append(a)

        out.append(
            {
                "source": "arxiv",
                "title": title,
                "url": link,
                "published": published,
                "authors": authors[:8],
                "summary": summary[:600],
            }
        )
    return out


def search_crossref(query: str, max_results: int = 5, timeout_s: int = 15) -> List[Dict[str, Any]]:
    params = urllib.parse.urlencode(
        {
            "query.bibliographic": query,
            "rows": max_results,
            "sort": "relevance",
            "order": "desc",
        }
    )
    url = f"https://api.crossref.org/works?{params}"
    obj = _get_json(url, timeout_s=timeout_s)

    items = obj.get("message", {}).get("items", [])
    out: List[Dict[str, Any]] = []
    for item in items:
        if not isinstance(item, Mapping):
            continue
        title_list = item.get("title")
        title = str(title_list[0]) if isinstance(title_list, list) and title_list else ""

        doi = item.get("DOI")
        url = str(item.get("URL") or "")
        if isinstance(doi, str) and doi.strip():
            url = f"https://doi.org/{doi.strip()}"

        published = ""
        issued = item.get("issued")
        if isinstance(issued, Mapping):
            date_parts = issued.get("date-parts")
            if isinstance(date_parts, list) and date_parts and isinstance(date_parts[0], list):
                published = "-".join(str(x) for x in date_parts[0][:3])

        authors: List[str] = []
        raw_authors = item.get("author")
        if isinstance(raw_authors, list):
            for a in raw_authors:
                if not isinstance(a, Mapping):
                    continue
                given = str(a.get("given") or "").strip()
                family = str(a.get("family") or "").strip()
                full = " ".join(x for x in (given, family) if x).strip()
                if full:
                    authors.append(full)

        container = ""
        container_titles = item.get("container-title")
        if isinstance(container_titles, list) and container_titles:
            container = str(container_titles[0])

        out.append(
            {
                "source": "crossref",
                "title": title,
                "url": url,
                "doi": str(doi or ""),
                "published": published,
                "authors": authors[:8],
                "journal": container,
            }
        )
    return out


def research_claim(
    claim: Mapping[str, Any],
    max_results: int = 5,
    timeout_s: int = 15,
) -> Dict[str, Any]:
    query = build_query_from_claim(claim)
    out: Dict[str, Any] = {
        "generated_at": _now_iso(),
        "query": query,
        "sources": {"arxiv": [], "crossref": []},
        "errors": [],
    }

    try:
        out["sources"]["arxiv"] = search_arxiv(
            query,
            max_results=max_results,
            timeout_s=timeout_s,
        )
    except Exception as e:  # pragma: no cover - network dependent
        out["errors"].append(f"arxiv: {e}")

    try:
        out["sources"]["crossref"] = search_crossref(
            query,
            max_results=max_results,
            timeout_s=timeout_s,
        )
    except Exception as e:  # pragma: no cover - network dependent
        out["errors"].append(f"crossref: {e}")

    return out
