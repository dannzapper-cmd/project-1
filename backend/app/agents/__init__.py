"""LeadForge agent runtime services (Phase 5.5+).

This package holds executable agent services that orchestrate the
existing Phase 5.2 contracts (``app.schemas.agents``) through the
Phase 5.4 model service abstraction (``app.services.model_service``).

The Phase 5.5A scope introduces only the Research Agent service, which
runs against ``MockModelService`` only. No real model provider is wired
in here. Subsequent phases (5.5B+) will broaden the agent roster and,
later, swap the mock provider for real ones.
"""
