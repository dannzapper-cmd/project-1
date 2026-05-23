"""Verify demo lead_id consistency between leads.csv and company_research.json."""

from __future__ import annotations

import csv
import json
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_LEADS_CSV = _REPO_ROOT / "data" / "demo" / "leads.csv"
_COMPANY_RESEARCH_JSON = _REPO_ROOT / "data" / "demo" / "company_research.json"


def _load_lead_ids_from_csv(path: Path) -> list[str]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [row["lead_id"] for row in reader if row.get("lead_id")]


def _load_lead_ids_from_research(path: Path) -> list[str]:
    records = json.loads(path.read_text(encoding="utf-8"))
    return [record["lead_id"] for record in records if record.get("lead_id")]


def _assert_no_duplicates(lead_ids: list[str], source: str) -> set[str]:
    seen: set[str] = set()
    duplicates: list[str] = []
    for lead_id in lead_ids:
        if lead_id in seen:
            duplicates.append(lead_id)
        seen.add(lead_id)
    assert not duplicates, f"Duplicate lead_ids in {source}: {sorted(set(duplicates))}"
    return seen


def test_demo_lead_ids_match_between_leads_and_research() -> None:
    csv_ids = _load_lead_ids_from_csv(_LEADS_CSV)
    research_ids = _load_lead_ids_from_research(_COMPANY_RESEARCH_JSON)

    csv_set = _assert_no_duplicates(csv_ids, "data/demo/leads.csv")
    research_set = _assert_no_duplicates(research_ids, "data/demo/company_research.json")

    missing_research = sorted(csv_set - research_set)
    extra_research = sorted(research_set - csv_set)

    assert csv_set == research_set, (
        "Demo lead_id mismatch between leads.csv and company_research.json. "
        f"Missing research for: {missing_research or 'none'}. "
        f"Extra research records: {extra_research or 'none'}."
    )
