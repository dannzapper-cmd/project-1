"""Shared JSON-extraction utilities (Phase 5.6B).

Single source of truth for parsing JSON objects out of LLM responses
across every LeadForge agent (Research, Qualifier, and any future
agent). Lives in ``app.services`` so agents never import from each
other — only from shared utilities (Phase 5.6B FIX 1).

Hard rules for this module:

* No agent imports here. No FastAPI imports. No model service imports.
  Pure stdlib only.
* No ``eval``, no ``ast.literal_eval``, no YAML, no third-party
  parsers, no regex. The agent test suites audit this module's source
  for those substrings.
* Behaviour is identical to the verbatim algorithm shipped in Phase
  5.5C inside ``research_agent.py`` — the function was moved here
  unchanged so existing Research Agent tests pass without weakening.
"""

from __future__ import annotations

import json


def extract_json_object(text: str) -> dict:
    """Best-effort JSON-object extraction from an LLM response.

    Three explicit attempts, in order, with stdlib ``json`` only — no
    regex, no ``eval``, no ``ast.literal_eval``, no YAML, no
    third-party parsers:

    1. ``json.loads(text)`` on the stripped string.
    2. If the string contains markdown code fences, strip them (and an
       optional ``json`` language tag) and try again.
    3. Take the substring from the first ``{`` to the last ``}`` and
       try ``json.loads`` on that.

    Raises
    ------
    ValueError
        If none of the three attempts produces a JSON object.
    """

    text = text.strip()

    # Attempt 1: parse the whole response.
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Attempt 2: strip markdown code fences (with optional `json` tag).
    if "```" in text:
        start = text.find("```")
        end = text.rfind("```")
        if start < end:
            inner = text[start + 3 : end].strip()
            if inner.startswith("json"):
                inner = inner[4:].strip()
            try:
                return json.loads(inner)
            except json.JSONDecodeError:
                pass

    # Attempt 3: first { to last }.
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and start < end:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass

    raise ValueError("No valid JSON object found in model response.")


__all__ = ["extract_json_object"]
