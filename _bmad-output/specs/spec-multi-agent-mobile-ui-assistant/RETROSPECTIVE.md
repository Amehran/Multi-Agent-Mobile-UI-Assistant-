---
date: 2026-08-26
verdict: accepted-with-open-items
criteria: declared
headless: false
---

# Retrospective: Self-Correcting Generation Pipeline (spec-multi-agent-mobile-ui-assistant)

## Epic summary

- **Spec folder:** `_bmad-output/specs/spec-multi-agent-mobile-ui-assistant/` (stories mode — `SPEC.md`, `stories.yaml`, `stories/1-4-*.md`).
- **Stories:** all 4 `done` — no `pending_stories`.
  1. In-graph validator with bounded retry loop — `3dc054e^..0df76e4` (commit `0df76e4`)
  2. Structured trace and verdict shapes — `0df76e4..210b546` (commit `210b546`)
  3. Streamlit trace panel and verdict rendering — `210b546..6c8ca24` (commit `6c8ca24`)
  4. Curated demo prompts and README pipeline correction — `6c8ca24..e05e22d` (commit `e05e22d`)
- **Full epic diff range:** `3dc054e^..e05e22d`, 4 commits (one per story, no merges).
- **Files most touched:** `ui_generator.py` (stories 1-3, +252 net lines, 815→1067), `streamlit_interface.py` (stories 3-4), `tests/test_ui_generator.py`, `tests/test_streamlit_interface.py`.
- **Evidence available:** all 4 story specs with frozen intent + Code Map; per-story `git_evidence.py` output; SPEC.md with a declared Success Signal; ARCHITECTURE-SPINE.md (AD-1..AD-5). **Missing:** no persisted session-log artifacts (the implementing session is this same conversation, not an exported log) — process-lesson analysis below relies on each story's own recorded review findings, not a transcript. No previous retrospective exists (first epic for this project).

## Behavior verification

Ran the pipeline live (local Ollama, `llama3.2`, zero API cost) rather than trusting mocked tests alone:

| Prompt | Compiled | Trace (5 nodes, in order) | Retries |
|---|---|---|---|
| Curated #1 (login) | ✅ | ✅ | 0 |
| Curated #2 (product card) | ✅ | ✅ | 0 |
| Curated #3 (settings) | ✅ | ✅ | 0 |
| Off-script (weather app) | ✅ | ✅ | 0 |

All 4 produced valid `@Composable` code with a full `ui_generator→validator→accessibility_reviewer→ui_reviewer→output` trace and generic pass/fail/warn verdicts. This directly satisfies SPEC.md's declared Success Signal. Not exercised live: the retry-loop path with a real LLM actually failing (all 4 live runs passed validation on the first attempt — the retry loop's live behavior is unit-tested with mocked failures only, never observed end-to-end with genuine LLM output).

## Findings

Consolidated from `bmad-review` (adversarial, edge-case, verification-gap lenses) run over the full epic diff, explicitly weighted toward story-to-story seams. Each carries its source and disposition.

### Cross-story seam findings

**F1 — Refine leaves the Trace/Validation Report tabs stale and misleading.**
Story 3 added `current_trace`/`current_validation_checks`/`validation_report` session-state fields and gave `current_accessibility`/`current_design` a dual-shape guard (`render_review`) specifically because `refine_ui` (pre-existing, untouched) writes prose into those two fields. But `refine_ui` never resets the three *new* fields story 3 introduced — after Generate → Refine, the Trace and Validation Report tabs keep showing the pre-refine generation's data as if it describes the refined code. Confirmed independently by the adversarial lens (`streamlit_interface.py:396-399` vs `:258,261,263` vs `:811-882`) and the edge-case lens (`streamlit_interface.py:816-818`).
Source: `src/multi_agent_mobile_ui_assistant/streamlit_interface.py:396-399`, `:258`, `:261`, `:263`.
Disposition: **fixed** (post-retro). Reset `current_trace`/`current_validation_checks`/`validation_report` in `refine_ui`'s success path; regression test `TestRefineUiClearsStaleTraceAndValidation`.
Process lesson: story 3's own spec boundaries only named `current_accessibility`/`current_design` for the refine-compatibility guard because that's the pair the crash-bug review caught — the spec never asked "what happens to *every* new session-state field story 3 introduces when the untouched sibling function that predates it runs afterward?" A story that adds new session-state alongside an explicitly-out-of-scope function should enumerate every new field's behavior under that function, not just the one a bug surfaced.

**F2 — `validation_checks` accumulates across retries with no per-attempt marker.**
Story 2 gave `validation_checks` an `operator.add` reducer so it accumulates every retry's `CheckResult`s (a deliberate fix from story 2's own review). Story 3 renders the accumulated list flatly. Result: a retried run shows two "compilation" verdicts (one `fail`, one `pass`) with nothing distinguishing which attempt produced which — raised independently by the adversarial lens (findings #5/#6) and the edge-case lens (2 of its 4 findings), the single most-corroborated finding across both lenses.
Source: `src/multi_agent_mobile_ui_assistant/ui_generator.py:801-818` (CheckResult construction, no attempt field); `streamlit_interface.py` render call sites.
Disposition: **fixed** (post-retro). Added `attempt: NotRequired[int]` to `CheckResult`, populated by `validator_node`, rendered as an `(attempt N)` prefix in `render_check_results`; regression assertions added to `test_validation_checks_accumulate_across_retries`.
Process lesson: when story 2 decided *what* accumulates across retries, it didn't decide *how a consumer would distinguish attempts* — a producer-side accumulation decision needs a consumer-legible discriminant from the start, not bolted on after a later story renders it.

**F3 — Figma and multi-file generation modes bypass the validator/retry loop entirely, and now render "No checks recorded" — indistinguishable from "checks passed."**
Pre-existing (Figma/multi-file never routed through `validator_node`), but story 3's generic `render_check_results`/`render_review` fallback message ("No checks recorded.") reads as a clean bill of health for a mode where no check ever ran, versus a mode where checks ran and passed. Raised by the adversarial lens (#7, #8) and the edge-case lens.
Source: `streamlit_interface.py:190-213` (Figma), `:226-234` (multi-file bypass); `streamlit_interface.py:133-135` (ambiguous empty-state message).
Disposition: message wording **fixed** (post-retro) — `accessibility_issues`/`design_issues`/`validation_checks` now set to `None` (not `[]`) for Figma/multi-file, and `render_check_results`/`render_review` render a distinct "Not run for this generation mode" message; regression test `test_multi_file_path_sets_check_fields_to_none_not_empty_list`. **Deferred**: the larger gap (Figma/multi-file never validated at all) — real, but a feature addition, not a quick patch.
Process lesson: none of stories 1-3 declared multi_file/Figma out of scope for validation explicitly — it was true by omission in each story's Code Map. A spec introducing a new cross-cutting check should say which existing generation modes it does and doesn't cover, not leave it implicit.

**F4 — Zero test coverage on the actual story-2→story-3 wiring (`generate_initial_ui`'s dict-unpacking).**
Story 2's producer-shape tests (`TestStructuredTraceAndVerdicts`) and story 3's renderer tests (`TestRenderCheckResults`, `TestRenderTraceSteps`, `TestRenderReview`) both use hand-built fixtures matching each other's assumed shape — neither test exercises `generate_initial_ui`, the actual glue that unpacks `generate_ui_from_description`'s dict into session state. A key rename (e.g. a `CheckResult.message`→`detail` copy-paste, given `TraceStep` sits right next to it) would pass every existing test and silently render blank rows or crash.
Source: verification-gap lens, confirmed via `grep -n "generate_initial_ui\|refine_ui\|reset_session"  tests/test_streamlit_interface.py` (zero matches).
Disposition: **fixed** (post-retro) — added `TestGenerateInitialUiWiring` (2 tests) exercising `generate_initial_ui`'s unpacking against a `generate_ui_from_description`-shaped fixture, including the multi-file `None`-vs-`[]` case.
Process lesson: this project has no precedent for testing Streamlit orchestration functions directly (confirmed repeatedly across all 3 code stories), which is a reasonable convention for UI rendering — but the *data-unpacking* logic inside those functions is plain Python with no Streamlit dependency and could be tested without an `AppTest` harness. The convention was applied too broadly.

### Single-story findings (real, not cross-story, worth recording)

**F5 — `validator_node`'s own MCP import sits outside its `try/except`, contradicting its documented "never crash the graph" guarantee.**
Source: `src/multi_agent_mobile_ui_assistant/ui_generator.py:756` (import) vs `:763` (try starts). Verified directly by re-reading the file.
Disposition: **fixed** (post-retro) — `AndroidLintMCP`/`GradleMCP` import moved inside the `try`; `CompilationResult` (needed unconditionally by the `except` handler) hoisted to a module-level import so it's always bound.

**F6 — The same `try/except` unconditionally resets `lint_issues = []` on any exception, discarding real lint results if `auto_fix`/`check_compilation` raises after `validate_compose_code` already succeeded.**
Source: `ui_generator.py:767` (real assignment) vs `:781` (unconditional reset in `except`). Verified directly.
Disposition: **fixed** (post-retro) — `lint_issues = []` now initialized before the `try`; the `except` handler no longer resets it.

**F7 — Retry feedback (`last_validation_errors`) is only spliced into the LLM-generation branch, never the template/fallback branches.**
Source: `ui_generator.py` — splice lives in the `else:` (LLM) branch; the non-LLM template branch and the LLM-exception fallback never see it.
Disposition: **defer** — the template/fallback path is a rarely-exercised code path (real LLM calls are the demoed path); real but low-priority.

**F8 — An LLM-exception fallback template can pass validation and reach output looking like a successful generation, with nothing in the trace/CheckResults flagging that generation itself failed.**
Source: `ui_generator.py` fallback-to-template path + `validator_node`'s pass-forward-regardless logic.
Disposition: **defer** — needs a small design decision (a `"check": "generation"` CheckResult) rather than a one-line fix.

**F9 — README's compilation-check description (added this epic, story 4) states kotlinc is tried first with heuristic fallback; the actual code runs the heuristic first and only tries `kotlinc` if the heuristic found zero errors — the precedence is reversed from what the doc now says.**
Source: README.md (story-4 diff) vs `android_tools_mcp.py:209-252` (`check_compilation`, untouched by any story this epic). This is a residual inaccuracy in this epic's own doc fix — the *previous* claim ("never real compilation") was corrected in story 4's review, but the corrected wording still gets the order of operations backwards.
Disposition: **fixed** (post-retro) — README reworded to state the actual precedence (heuristic first, `kotlinc` only attempted when the heuristic finds nothing).

### Accepted deviations (already evaluated, not re-flagging)

- Unrecognized `LintIssue.severity` silently defaulting to `"warn"` — raised and evaluated during story 2's own review; `severity` is closed to 3 values in the only producer (`android_tools_mcp.py`), so currently unreachable. Accepted as-is.
- `auto_fixed` flag meaning "issues were found" rather than "issues were fixed" — pre-existing quirk from before this epic, evaluated during story 1's review as out of scope (preserving the locked `validation_report` shape). Accepted as-is.
- Multi-file + `validate=True` + `return_report=True` losing the multi-file breakdown — pre-existing, tracked in `deferred-work.md` since story 1, re-confirmed unaffected by stories 3-4's `not multi_file` guard.
- No automated sync check between `CURATED_DEMO_PROMPTS` and README's prompt copy (adversarial #12) — real but low-value; **defer**.

## Previous-retro follow-through

No previous retrospective exists for this project — this is the first epic. Nothing to follow through on.

## Action items

| # | Item | Finding | Owner | Status |
|---|---|---|---|---|
| 1 | Reset `current_trace`/`current_validation_checks`/`validation_report` in `refine_ui`'s success path | F1 | dev | **done** |
| 2 | Add an `attempt`/`retry_count` field to `CheckResult`, render it in the Validation Report tab | F2 | dev | **done** |
| 3 | Distinguish "validation not run" from "validation passed" in `render_check_results`/`render_review` empty state (pass `None` vs `[]`) | F3 | dev | **done** |
| 4 | Add a test covering `generate_initial_ui`'s unpacking of `generate_ui_from_description`'s dict shape | F4 | dev | **done** |
| 5 | Move the `android_tools_mcp` import inside `validator_node`'s `try` block | F5 | dev | **done** |
| 6 | Initialize `lint_issues = []` before `validator_node`'s `try`, stop resetting it in `except` | F6 | dev | **done** |
| 7 | Correct README's compilation-check precedence description (heuristic-first, not kotlinc-first) | F9 | dev | **done** |
| 8 (deferred) | Route Figma/multi-file code through `validator_node` too, or explicitly label them as unvalidated | F3 | future story | open |
| 9 (deferred) | Splice retry feedback into template/fallback generation branches | F7 | future story | open |
| 10 (deferred) | Tag LLM-exception-fallback generations distinctly in trace/CheckResults | F8 | future story | open |
| 11 (deferred) | Add a test asserting `CURATED_DEMO_PROMPTS` stays in sync with README | accepted deviation | future story | open |

All 7 fix-now items were applied and verified in the same session (commit follows), with regression tests: `test_validation_checks_accumulate_across_retries` (attempt field), `TestGenerateInitialUiWiring` (2 tests), `TestRefineUiClearsStaleTraceAndValidation`, `test_multi_file_path_sets_check_fields_to_none_not_empty_list`. Full suite: 151/151 passing (`--ignore=tests/test_mcp_tools.py`); app boots clean.

Process lessons (upstream, for future spec-writing on this project): a story adding new session-state alongside an out-of-scope sibling function must enumerate *every* new field's behavior under that function, not just the one a bug happened to surface (F1); a producer-side accumulation decision (retry-loop lists) needs a consumer-legible discriminant decided at the same time, not bolted on later (F2); a spec introducing a cross-cutting check should state which existing modes it does/doesn't cover rather than leaving it implicit (F3).

## Acceptance verdict

**accepted-with-open-items**, criteria **declared** (SPEC.md's `## Success signal`).

- All 4 stories `done`, no unfinished work.
- Declared Success Signal demonstrably met: verified live (see Behavior verification) — all 3 curated prompts plus one off-script prompt compiled, produced a full 5-node trace, and rendered generic pass/fail/warn verdicts, reproducibly, without manual intervention.
- No finding blocks the declared criteria — F1-F9 are real and worth fixing, but none prevent the demoed golden path from working as specified. F1 (stale tabs after Refine) is the one most likely to visibly embarrass a live demo if a refine step is shown, which is why it's the top action item.

## Open questions

- Should Figma-imported and multi-file-generated code eventually go through the same validator/retry loop as the standard text path (F3's deferred half), or is that explicitly out of scope for this pipeline's self-correction story? Affects whether F3's deferred item becomes a future story.
- Is a per-attempt marker on `CheckResult` (F2) the right shape, or should retried attempts be nested under their own `TraceStep` instead? Both close the gap; the retro didn't pick one since it's a design call.

## Assumptions

None — this run was interactive throughout (epic/spec folder was named directly, all dispositions and the verdict were made by the retrospective analysis itself; no user confirmation was skipped that the workflow requires).
