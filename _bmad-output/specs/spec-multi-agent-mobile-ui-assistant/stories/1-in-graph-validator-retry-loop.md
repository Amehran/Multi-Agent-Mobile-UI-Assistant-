---
title: 'In-graph validator with bounded retry loop'
type: 'feature'
created: '2026-08-25'
status: 'done'
review_loop_iteration: 0
context: []
baseline_commit: '3dc054edd8f0c092c6651e4c6223225556a6cd84'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Validation runs post-hoc, outside the LangGraph `StateGraph` (after `app.invoke()` returns), and is duplicated by a separate ad-hoc auto-fix inside `ui_generator_agent`. Neither path can route a failure back into regeneration, so the pipeline's core "self-check and recover" claim (CAP-4) isn't structurally real.

**Approach:** Add a `validator` node between `ui_generator` and `accessibility_reviewer` in the compiled graph. A conditional edge routes back to `ui_generator` on compilation failure while `retry_count < 2`, carrying the failure reason into the regeneration prompt; otherwise it proceeds forward regardless of pass/fail. Remove the two now-redundant validation paths in favor of this single one.

## Boundaries & Constraints

**Always:**
- `validator` node wraps `AndroidLintMCP.validate_compose_code` + `AndroidLintMCP.auto_fix` + `GradleMCP.check_compilation` (`android_tools_mcp.py`).
- Validation only executes when `state["validate_code"]` is true (see Ask First — resolved as opt-in); when false, `validator` is a pass-through (no lint/compile calls, no retry).
- Retry triggers only on `not compilation.success` after auto-fix has already run; a bounded `state["retry_count"]` (int, default 0) increments each loop-back and caps at 2 — on the 3rd attempt the graph proceeds forward regardless of outcome (demo must always complete).
- `state["last_validation_errors"]` (list of compilation error strings) is set on failure and spliced into `ui_generator_agent`'s prompt (in `user_message_parts`, before the join at ui_generator.py:295) so the retry targets the specific failure.
- Remove `ui_generator_agent`'s in-agent `validate_code` auto-fix branch (ui_generator.py:379-385) and the post-hoc validation block in `generate_ui_from_description` (ui_generator.py:713-764) — both are superseded by the graph-level `validator` node.
- `generate_ui_from_description`'s external return shape is unchanged for all `validate`/`return_report` combinations (str, multi-file dict, or `{"code", "validation_report": {"lint_issues", "lint_issues_count", "auto_fixed", "compilation"}}`) — same field names, now sourced from final graph state instead of a post-hoc computation.

**Ask First:** None remaining — validation stays opt-in behind `validate_code`/`validate=True` (confirmed with human; default behavior for non-validating callers like `main.py` is unchanged).

**Never:**
- Do not invoke real `kotlinc`/Gradle — `GradleMCP.check_compilation`'s brace-counting heuristic is unchanged (architecture Deferred).
- Do not reintroduce Intent Parser/Layout Planner nodes or split generation into multiple LLM calls (AD-1).
- Do not add new external dependencies (`langgraph>=1.0.3` already supports `add_conditional_edges`).
- Do not introduce the structured `CheckResult`/trace shapes here — that's story 2's scope; this story's `last_validation_errors` stays a plain list of strings.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| `validate=False` (e.g. `main.py`) | Default call, no flags | Identical to current behavior — `validator` no-ops, no retry | N/A |
| Valid code, first try | `validate=True`, generated code compiles | `validator` passes, `retry_count` stays 0, proceeds to `accessibility_reviewer` | N/A |
| Fails once, fixed on retry | `validate=True`, first generation fails compilation | `retry_count` → 1, `last_validation_errors` set, `ui_generator` regenerates using that feedback, second attempt passes | N/A |
| Retries exhausted | Code still fails after 2 retries | Graph proceeds forward anyway with `retry_count == 2` and `last_validation_errors` populated in final state/output | Never blocks demo completion |

</frozen-after-approval>

## Code Map

- `src/multi_agent_mobile_ui_assistant/ui_generator.py:25-38` -- `UIGeneratorState` TypedDict; add `retry_count: int` and `last_validation_errors: list[str]`.
- `src/multi_agent_mobile_ui_assistant/ui_generator.py:44-391` (`ui_generator_agent`) -- splice retry feedback into `user_message_parts` before the join at line 295; remove in-agent auto-fix branch at 379-385.
- `src/multi_agent_mobile_ui_assistant/ui_generator.py:618-645` (`build_ui_generator_graph`) -- add `validator` node + `add_conditional_edges` for the retry loop-back.
- `src/multi_agent_mobile_ui_assistant/ui_generator.py:652-764` (`generate_ui_from_description`) -- remove the post-hoc validation block (713-764); assemble the same return shapes from final graph state instead.
- `src/multi_agent_mobile_ui_assistant/android_tools_mcp.py:16-30,57,128,199` -- `LintIssue`, `CompilationResult`, `validate_compose_code`, `auto_fix`, `check_compilation` — reused as-is, no changes.
- `streamlit_interface.py:175-186` -- caller; reads `output['code']` / `output.get('validation_report')` — must keep working unchanged.
- `main.py:23` -- caller with no flags; must keep receiving a plain str.
- `tests/test_ui_generator.py:507-654` (`TestValidationPipeline`) -- 6 tests assert the current post-hoc dict shape; rework to assert against the new graph-level path (same shape, new source).
- `tests/test_ui_generator.py:551` (`test_ui_generator_agent_applies_auto_fix`) -- tests the in-agent auto-fix branch being removed; rewrite or remove.
- `tests/test_ui_generator.py:318-333` (`TestGraphBuilder`) -- must still pass with the new node/edges added.

## Tasks & Acceptance

**Execution:**
- [x] `ui_generator.py` -- add `retry_count`/`last_validation_errors` to `UIGeneratorState` -- carries retry bookkeeping through the graph
- [x] `ui_generator.py` -- implement `validator_node` (pass-through when `validate_code` false; else lint→auto-fix→compile) -- single source of validation truth
- [x] `ui_generator.py` -- wire `validator` into `build_ui_generator_graph` with conditional retry edge back to `ui_generator` (cap 2) -- makes self-correction structurally real (CAP-4)
- [x] `ui_generator.py` -- splice `last_validation_errors` into `ui_generator_agent`'s prompt on retry -- targets regeneration at the actual failure
- [x] `ui_generator.py` -- remove in-agent auto-fix branch (379-385) and post-hoc block (713-764); reassemble `generate_ui_from_description`'s return shapes from final state -- one validation path, same external contract
- [x] `tests/test_ui_generator.py` -- rework `TestValidationPipeline` and `test_ui_generator_agent_applies_auto_fix` against the new path; add a retry-loop test (fails once, passes on retry) and a retries-exhausted test -- covers the I/O matrix

**Acceptance Criteria:**
- Given `validate=False`, when generating UI, then output is unchanged from current behavior (no validator side effects).
- Given `validate=True` and code that fails compilation once, when generated, then `retry_count` reaches 1, `last_validation_errors` is non-empty at that point, and the retried generation is attempted with that feedback in its prompt.
- Given `validate=True` and code that fails compilation on every attempt, when generated, then the graph completes (does not hang or error) after `retry_count` reaches 2.
- Given `return_report=True`, when generation completes, then the returned dict's `validation_report` keys (`lint_issues`, `lint_issues_count`, `auto_fixed`, `compilation`) are present with the same shape as before this change.

## Verification

**Commands:**
- `uv run pytest tests/test_ui_generator.py -v` -- expected: all tests pass, including reworked `TestValidationPipeline` and new retry-loop tests.
- `uv run pytest tests/ -v` -- expected: full suite passes (no regression in `streamlit_interface`/other tests depending on `generate_ui_from_description`'s shape).
