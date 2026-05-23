# ADR-001: LangGraph Integration Decision

## Status
Deferred

## Context
LeadForge-Agentic Core ships a five-agent B2B sales-intelligence pipeline
(Research → Qualifier → Strategist → Email Drafter → QA Evaluator). The
pipeline is currently orchestrated by a small, deterministic, plain-Python
service (`backend/app/services/pipeline_service.py`) introduced in Phase
6.1 and extended for batch in Phase 6.2.

LangGraph is a popular agent-orchestration runtime that adds a graph-based
execution model with branching, conditional edges, retries, persistent
state, and tool routing. It is a natural fit when an agent system has
real branching logic, durable state, or parallel tool calls. It is a
heavy-weight dependency when none of those capabilities are required.

Block 8.3 introduces a controlled live Groq single-lead pipeline path on
top of the existing deterministic chain. The live path:

* runs exactly one lead per request,
* re-uses the same agent contracts as the deterministic baseline,
* swaps the model service for `GroqModelService` only inside the agents
  that already support `use_model_synthesis=True`,
* returns the deterministic baseline alongside the live result so the
  two outputs can be compared directly,
* never silently falls back to deterministic output when the live run
  fails — failures are surfaced as `live_success=false` with explicit
  `failed_agent`, `failure_stage`, and `error_code` fields.

This shape is well-served by linear, in-process orchestration. There is
no branching beyond "live succeeded vs live failed", no durable retries,
no parallel tool fan-out, and no human-review state machine in the
backend. The deterministic pipeline already provides:

* a deterministic baseline,
* a test oracle (every agent service has unit + contract tests),
* replay/demo safety (no network call by default),
* a comparison target for the new live path.

Adding a graph runtime now would increase dependency surface, cognitive
overhead, and orchestration complexity without unlocking a capability
the product currently needs. It would also push us towards orchestration
patterns (durable state, persistent checkpoints, retries with backoff)
that are explicitly out of scope for the portfolio version of this
project.

## Decision
Defer LangGraph adoption.

Block 8.3 implements the controlled live Groq single-lead path using the
existing plain-Python orchestration service. No `langgraph` dependency
is added to `backend/requirements.txt`. No new runtime, graph compiler,
or checkpoint store is introduced. The pipeline remains a small,
auditable, in-process function call.

The decision is not a permanent rejection of LangGraph — it is gated
behind concrete product/architecture triggers (see *Revisit criteria*).
When one or more of those triggers becomes real, this ADR will be
re-evaluated and superseded.

## Consequences

### Going forward this means
* Block 8.3 keeps orchestration trivial: live mode adds one new service
  module (`live_pipeline_service.py`) and one POST endpoint. Tests can
  exercise the orchestration end-to-end with an in-process stub model
  service.
* No new dependency, no new runtime to maintain, no new failure mode in
  CI.
* The deterministic baseline remains the canonical test oracle. The
  live path is structured so that swapping its underlying orchestration
  later does not change the public response schema (`LivePipelineResponse`,
  `LivePipelineComparison`).
* Future agent additions (e.g. a Smart Intake step, a deeper research
  step) can still slot into the linear pipeline as long as the
  orchestration stays linear and stateless.

### Tradeoffs we accept
* No automatic per-agent retry, no backoff, no checkpoint replay. The
  Block 8.3 prompt explicitly forbids retry logic in this PR; this ADR
  reflects that constraint.
* No conditional edge logic. If a future agent needs to branch (for
  example, choose between two strategist sub-agents), the linear
  orchestration must either be extended carefully or we must revisit
  this ADR.
* No parallel tool fan-out. Live web research, multi-source enrichment,
  and parallel evidence gathering would push us out of "linear pipeline"
  territory and toward a graph runtime.

## Revisit criteria
Re-evaluate this ADR when *any* of the following becomes a real
product or architecture requirement:

* **Branching agent logic.** A pipeline step needs to choose between
  two or more downstream paths based on a runtime condition (for
  example, route between an SMB and an enterprise strategist) and the
  routing logic is non-trivial.
* **Stateful retries.** Per-agent retry with exponential backoff,
  idempotency keys, and recovery semantics that survive a crash.
* **Durable human review persistence.** A backend-side review queue
  with checkpointable state across processes (today the human review
  step is local-only and stateless on the backend).
* **Live research with parallel tool calls.** Multiple concurrent
  enrichment / search / scraping calls feeding into a single research
  step, with structured aggregation and safe failure isolation.
* **Smart Intake with conditional normalization flows.** An intake
  agent that runs different normalization sub-pipelines depending on
  the source and shape of the raw lead.
* **Complex failure recovery.** A failure in agent N must trigger a
  bounded recovery sequence (re-run agent N-1 with adjusted inputs,
  or fall back to a different strategy) rather than fail the run as a
  whole.
* **More complex agent orchestration.** Loops, sub-graphs, conditional
  feedback edges, agent-to-agent message passing, or persistent
  in-flight state.

If two or more of these triggers land in the same block, that is a
strong signal to install LangGraph (or an equivalent graph runtime)
and migrate `pipeline_service.py` / `live_pipeline_service.py` onto
it.
