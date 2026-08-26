---
id: SPEC-multi-agent-mobile-ui-assistant
companions: ['../../planning-artifacts/architecture/architecture-Multi-Agent-Mobile-UI-Assistant--2026-08-25/ARCHITECTURE-SPINE.md']
sources: ['../../planning-artifacts/prds/prd-Multi-Agent-Mobile-UI-Assistant--2026-08-25/prd.md']
---

> **Canonical contract.** This SPEC and the files in `companions:` are the complete, preservation-validated contract for what to build, test, and validate. Source documents listed in frontmatter are for traceability — consult them only if you need narrative rationale or prose color this contract intentionally omits.

# Multi-Agent Mobile UI Assistant — Self-Correcting Generation Pipeline

## Why

A vision to realize: a portfolio demo proving the ability to design agents that self-check and recover from mistakes, not just chain prompts. The existing LangGraph pipeline generates Jetpack Compose/Kotlin code from natural language but runs validation post-hoc, outside the graph — so self-correction is not structurally demonstrable. This matters now because the repo is public and read by two audiences: a recruiter skimming for 30 seconds (needs an immediately legible result) and an engineer or hiring manager reading the orchestration code (needs to see real agent reasoning, checks, and recovery — not a polished facade).

## Capabilities

- **CAP-1**
  - **intent:** User submits a natural-language UI description; system generates valid Jetpack Compose/Kotlin code.
  - **success:** 3 curated demo prompts each produce compiling Compose code end-to-end without manual intervention.
- **CAP-2**
  - **intent:** Every pipeline node exposes its decision/output as a structured trace entry, so an agent-trace panel can show real reasoning as it happens.
  - **success:** For any run, the trace shows exactly one entry per node actually executed (`ui_generator`, `validator`, `accessibility_reviewer`, `ui_reviewer`, `output`) — no stages that don't exist in the graph.
- **CAP-3**
  - **intent:** Accessibility and Material 3 design checks are surfaced as an explicit pass/fail/warn verdict per check, not prose.
  - **success:** The verdict UI renders status generically off a structured field, with no string-sniffing of review text.
- **CAP-4**
  - **intent:** When validation fails, the system retries generation using the specific failure reason, bounded to a fixed number of attempts, and the retry is visible in the trace.
  - **success:** A demo prompt engineered to fail validation once visibly loops back, increments a retry counter, and the trace shows the corrected output — within 2 retries.
- **CAP-5** *(Should)*
  - **intent:** Render a visual HTML preview of the generated UI alongside the code. *(Already implemented — `streamlit_interface.py`.)*
  - **success:** A preview renders for every generated UI with no manual step.
- **CAP-6** *(Should)*
  - **intent:** Accept a Figma file/frame reference via the existing Figma MCP integration as an alternative input source. *(Already implemented.)*
  - **success:** A Figma-sourced input completes a generation run through the same pipeline as natural-language input.
- **CAP-7** *(Should)*
  - **intent:** Support iterative refinement of previously generated code via the Streamlit chat interface. *(Already implemented.)*
  - **success:** A follow-up instruction updates the prior code without a full restart.
- **CAP-8** *(Could)*
  - **intent:** Ship curated demo prompts that mix concrete requirements with subjective style language, to demonstrate genuine interpretation rather than template-filling.
  - **success:** 3 documented prompts exist and are the same 3 used in CAP-1's success signal.

## Constraints

- No new external dependencies — build on the existing stack (`langgraph>=1.0.3`, `streamlit>=1.39.0`, `langchain-core`/`langchain-openai`/`langchain-ollama`, `mcp`); `langgraph>=1.0.3` already supports the conditional-edge routing CAP-4 needs.
- Secrets (LLM API keys, Figma tokens) stay in `.env`, never committed — the repo is public.
- Real Kotlin compilation stays a heuristic (`GradleMCP` brace/paren counting, not an actual `kotlinc`/Gradle invocation) — must be documented as a known limitation, never presented as real compilation.
- Single-LLM-call generation is retained (architecture AD-1); the README's pipeline description must be corrected to match the real graph nodes rather than the fictitious Intent Parser/Layout Planner stages it currently names.
- All check-producing nodes return a shared `CheckResult{check, status: pass|fail|warn, message}` shape (AD-3); every node appends a shared `TraceStep{node, summary, detail}` to `state["trace"]` (AD-4); retry is capped at 2 attempts and carries `last_validation_errors` into the regeneration prompt (AD-2/AD-5). Full shapes and rationale: see the architecture companion.
- The generation loop must feel live/interactive during a demo — not a long silent batch wait with no progress feedback.
- When scope is ambiguous, favor making the pipeline's existing self-correction behavior visible over adding new capabilities.

## Non-goals

- Staged "break it live" failure theatrics for demo effect.
- New input modalities beyond natural-language text and Figma.
- Production-grade hardening: authentication, multi-user support, or persistent storage beyond a session.

## Success signal

3 curated demo prompts each run end-to-end in a single pass, reproducibly and without manual intervention, each producing compiling Compose code, a populated agent-trace panel, and a pass/fail self-review verdict. One additional off-script prompt also completes without breaking the pipeline — a counter-metric guarding against a demo that only works because it's rehearsed.

## Open Questions

- Exact wording of the 3 curated demo prompts (CAP-1/CAP-8) — to be decided during implementation/demo scripting.
