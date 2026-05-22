"""Model service schemas (Phase 5.4).

Schema-only leaf module. Defines the Pydantic v2 request/response, config,
provider, usage, cost, and error shapes that the model service layer
exposes — without implementing any actual provider call.

Architecture rules:

* No service logic in this module.
* No imports from FastAPI routes, ``simulation_service``,
  ``evaluation_service``, or ``agents.py``.
* No network clients (``requests`` / ``httpx`` etc.) imported anywhere.
* ``ModelProvider`` declares the future provider identifiers; only
  ``MOCK`` is implemented in Phase 5.4 (see ``model_service.py``).
* Phase 5.4 FIX 2: ``ModelMessage.content`` and ``ModelRequest.messages``
  use explicit Pydantic v2 ``Field`` constraints (``min_length=1``).
* The ``protected_namespaces=()`` config on models that use the
  ``model_name`` field is intentional: it silences Pydantic v2's
  ``model_`` protected-namespace warning without renaming a field that
  the future-provider contract genuinely calls "model name".
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


# --------------------------------------------------------------------------- #
# Enums                                                                       #
# --------------------------------------------------------------------------- #


class ModelProvider(str, Enum):
    """Future model providers.

    Only ``MOCK`` is implemented in Phase 5.4. ``OLLAMA``, ``GROQ`` and
    ``OPENAI`` are declared so contracts and routes can already reference
    them; ``get_model_service`` raises ``NotImplementedError`` for any
    non-mock provider so a real call cannot happen accidentally.
    """

    MOCK = "mock"
    OLLAMA = "ollama"
    GROQ = "groq"
    OPENAI = "openai"


class ModelRole(str, Enum):
    """Chat-message role, mirroring the convention every provider supports."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


# --------------------------------------------------------------------------- #
# Request schemas                                                             #
# --------------------------------------------------------------------------- #


class ModelMessage(BaseModel):
    """One chat message inside a ``ModelRequest``.

    ``content`` is non-empty by construction (FIX 2).
    """

    model_config = ConfigDict(extra="ignore")

    role: ModelRole
    content: str = Field(..., min_length=1)


class ModelConfig(BaseModel):
    """Per-call configuration for the model service.

    ``protected_namespaces=()`` silences Pydantic v2's warning about the
    ``model_name`` field, which is a deliberate part of the public
    provider contract and is not renamed.
    """

    model_config = ConfigDict(extra="ignore", protected_namespaces=())

    provider: ModelProvider = ModelProvider.MOCK
    model_name: str = "mock-leadforge-model"
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    max_tokens: int = Field(default=512, ge=1)
    timeout_seconds: int = Field(default=30, ge=1)
    cost_per_1k_input_tokens: float = Field(default=0.0, ge=0.0)
    cost_per_1k_output_tokens: float = Field(default=0.0, ge=0.0)


class ModelRequest(BaseModel):
    """Top-level request to the model service.

    ``messages`` must contain at least one ``ModelMessage`` (FIX 2).
    """

    model_config = ConfigDict(extra="ignore")

    messages: list[ModelMessage] = Field(..., min_length=1)
    config: ModelConfig = Field(default_factory=ModelConfig)
    request_id: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


# --------------------------------------------------------------------------- #
# Response / usage / cost schemas                                             #
# --------------------------------------------------------------------------- #


class ModelUsage(BaseModel):
    """Token-usage breakdown for one model call."""

    model_config = ConfigDict(extra="ignore")

    input_tokens: int = Field(..., ge=0)
    output_tokens: int = Field(..., ge=0)
    total_tokens: int = Field(..., ge=0)


class ModelCostEstimate(BaseModel):
    """Cost estimate for one model call.

    ``display_cost`` is the canonical string representation (formatted
    by ``estimate_model_cost`` in the service) used by UIs/exports.
    """

    model_config = ConfigDict(extra="ignore")

    input_cost: float = Field(..., ge=0.0)
    output_cost: float = Field(..., ge=0.0)
    total_cost: float = Field(..., ge=0.0)
    currency: str = "USD"
    display_cost: str


class ModelResponse(BaseModel):
    """Top-level response returned by every implementation of
    :class:`app.services.model_service.BaseModelService.complete`.

    ``simulated`` is ``True`` by default because, in Phase 5.4, only the
    mock provider is wired up. Real implementations must override this
    explicitly when they ship.
    """

    model_config = ConfigDict(extra="ignore", protected_namespaces=())

    request_id: str | None = None
    provider: ModelProvider
    model_name: str
    content: str
    usage: ModelUsage
    cost: ModelCostEstimate
    latency: str = "0ms"
    finish_reason: str = "stop"
    simulated: bool = True
    raw_response: dict | None = None


# --------------------------------------------------------------------------- #
# Error schema                                                                #
# --------------------------------------------------------------------------- #


class ModelServiceError(BaseModel):
    """Structured error surface for the model service layer.

    This is a *schema*, not an exception. The service raises stdlib
    exceptions (``NotImplementedError``, ``ValueError``); when a caller
    wants to forward a structured error to the client, it materializes
    one of these.
    """

    model_config = ConfigDict(extra="ignore")

    code: str
    message: str
    provider: ModelProvider | None = None
    recoverable: bool = True
    details: dict[str, str] = Field(default_factory=dict)
