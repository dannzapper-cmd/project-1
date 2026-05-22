"""Shared enums used across schemas.

Values mirror the frontend types in `lib/types.ts` so the API contract is
ready for the demo dashboard once endpoints are wired in Block 4.2+.
"""

from __future__ import annotations

from enum import Enum


class Priority(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class LeadStatus(str, Enum):
    PENDING_REVIEW = "Pending Review"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    NEEDS_EDIT = "Needs Edit"


class RunMode(str, Enum):
    LIVE = "Live"
    REPLAY = "Replay"
    # Phase 5.1 — Pipeline Simulation Layer. Lowercase value is intentional
    # so that simulation-only responses are visually distinct from the
    # existing capitalized "Live" / "Replay" modes and so that downstream
    # callers cannot accidentally treat a simulated run as a real one.
    SIMULATION = "simulation"


class Confidence(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class HallucinationRisk(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class AgentRunStatus(str, Enum):
    SUCCESS = "success"
    WARNING = "warning"
    FAILED = "failed"
    RUNNING = "running"
    PENDING = "pending"


class Recommendation(str, Enum):
    APPROVE = "Recommended for approval"
    REVIEW = "Review carefully"
    REGENERATE = "Regenerate suggested"


class EvidenceSource(str, Enum):
    KNOWLEDGE_BASE = "Knowledge Base"
    PUBLIC_DATA = "Public Data"
    DEMO_CONTEXT = "Demo Context"
