---
title: 'Curated demo prompts and README pipeline correction'
type: 'chore'
created: '2026-08-26'
status: 'done'
route: 'one-shot'
baseline_commit: '6c8ca241ae64a6650b15220d67290dbf5adb5d96'
---

# Curated demo prompts and README pipeline correction

## Intent

**Problem:** CAP-8 needed 3 documented demo prompts mixing concrete requirements with subjective style cues (to demonstrate genuine interpretation, not template-filling), and the README's architecture description/diagram still named a fictitious "Intent Parser"/"Layout Planner" preprocessing stage that AD-1 explicitly removed — misleading anyone reading the orchestration code. The Gradle MCP compilation-check claim was also inaccurate: it actually attempts real `kotlinc` compilation when available, falling back to a heuristic only when the binary is missing, not "never real compilation" as originally assumed.
**Approach:** Rewrote the README's feature bullets and Mermaid diagram to match the real graph (`ui_generator → validator ⟲ → accessibility_reviewer → ui_reviewer → output`); added an accurate known-limitation note about the compilation check's conditional real-kotlinc/heuristic behavior; added the 3 curated demo prompts to the README and wired them as one-click sidebar buttons in `streamlit_interface.py` (via a shared `CURATED_DEMO_PROMPTS` constant), alongside the pre-existing generic example prompts.

## Suggested Review Order

**Pipeline description accuracy**

- Corrected architecture bullets: single-LLM-call generator + in-graph validator retry loop replace the fictitious Intent Parser/Layout Planner.
  [`README.md:16`](../../../../README.md#L16)

- Mermaid diagram now matches the real graph topology, including the bounded retry edge.
  [`README.md:36`](../../../../README.md#L36)

- Corrected the Gradle MCP compilation-check claim after verifying `_try_kotlinc` actually runs when available — it's conditional, not always a heuristic.
  [`README.md:122`](../../../../README.md#L122)

**Curated demo prompts (CAP-8)**

- Documents the 3 curated prompts and their intent (concrete + subjective style mix).
  [`README.md:124`](../../../../README.md#L124)

- Single source of truth for the 3 prompt strings, reused by the sidebar buttons.
  [`streamlit_interface.py:27`](../../../../src/multi_agent_mobile_ui_assistant/streamlit_interface.py#L27)

- Sidebar wiring: clicking a curated prompt populates the description input, same pattern as the existing example prompts.
  [`streamlit_interface.py:725`](../../../../src/multi_agent_mobile_ui_assistant/streamlit_interface.py#L725)

**Peripheral**

- Project Structure entry for `ui_generator.py` updated to reflect the pipeline redesign.
  [`README.md:159`](../../../../README.md#L159)
