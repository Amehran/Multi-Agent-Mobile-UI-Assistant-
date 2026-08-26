---
title: 'Structured trace and verdict shapes'
type: 'feature'
created: '2026-08-26'
status: 'done'
review_loop_iteration: 0
context: []
baseline_commit: '0df76e4f5f66af58133e921abd2512f807af2a75'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Every check-producing node emits ad-hoc prose strings (`accessibility_issues`/`design_issues` are `list[str]`, `ui_reviewer_agent` even mixes "Good: ..." praise into the same list as failures), and no node records its reasoning as structured state — pipeline behavior is only observable via `print()`. Neither an agent-trace panel nor a generic pass/fail/warn verdict UI is buildable on top of this.

**Approach:** Introduce two shared TypedDict shapes in `ui_generator.py`: `TraceStep{node, summary, detail}` and `CheckResult{check, status: pass|fail|warn, message}`. Every graph node appends one `TraceStep` to `state["trace"]`. `validator_node`, `accessibility_reviewer_agent`, and `ui_reviewer_agent` emit `CheckResult` lists instead of prose.

## Boundaries & Constraints

**Always:**
- Add `trace: Annotated[list, operator.add]` to `UIGeneratorState` (same accumulation pattern as the existing `messages: Annotated[list, add_messages]`); every node (`ui_generator`, `validator`, `accessibility_reviewer`, `ui_reviewer`, `output`) returns `{"trace": [TraceStep(...)], ...}` alongside its existing return keys — never the full list, LangGraph's reducer appends it.
- `accessibility_reviewer_agent`'s `accessibility_issues` and `ui_reviewer_agent`'s `design_issues` become `list[CheckResult]`: preserve every existing detection condition (content description, touch target, semantics, MaterialTheme, padding, Arrangement, Alignment) as one `CheckResult` each; "Good: ..." strings become `status="pass"`, "Consider ..." strings become `status="warn"`, the existing `not issues` fallback becomes a single `status="pass"` CheckResult so the list is never empty.
- `validator_node` additionally returns `validation_checks: list[CheckResult]`: map each `LintIssue` (`android_tools_mcp.py:16-22`, `severity` ∈ error/warning/info → fail/warn/pass) plus one `CheckResult` for `compilation_result` (`check="compilation"`, pass/fail on `.success`). Leave `lint_issues`/`compilation_result` (raw dataclasses) untouched — `generate_ui_from_description`'s `validation_report` dict (locked by story 1) keeps reading those, not `validation_checks`.
- `output_node` keeps producing a prose `final_output` string (external contract for the default/`return_report=False` path is unchanged) by rendering each `CheckResult.message` under the same `"ACCESSIBILITY REVIEW"` / `"DESIGN REVIEW (Material 3 Guidelines)"` banners it uses today, so `streamlit_interface.py`'s `extract_section` (lines 199-200) keeps matching until story 3 reworks the UI side.
- `generate_ui_from_description`'s external return shapes (str / multi-file dict / `{"code", "validation_report"}`) stay exactly as story 1 left them — `trace`/`validation_checks` are new internal state, not new external return fields.

**Ask First:** None.

**Never:**
- Do not touch `streamlit_interface.py` — rendering `trace`/`CheckResult` in the UI is story 3's scope.
- Do not change `validation_report`'s dict shape (`lint_issues`, `lint_issues_count`, `auto_fixed`, `compilation`) — that contract is locked by story 1.
- Do not add new external dependencies; `operator.add` is stdlib.
- Do not change `MAX_VALIDATION_RETRIES`/retry semantics — story 1's scope, untouched here.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Full run, no validation | `validate_code=False` | `state["trace"]` has exactly 4 entries (`ui_generator`, `validator`, `accessibility_reviewer`, `ui_reviewer`... plus `output` = 5), one per node actually executed | N/A |
| Retry loop (validate_code=True, fails once) | Same code path as story 1's retry test | `trace` has 2 `ui_generator` entries + 2 `validator` entries (one per pass) + 1 each for the rest — no missing/duplicated node beyond actual executions | N/A |
| Code with no accessibility/design findings | Clean generated code | `accessibility_issues`/`design_issues` each contain exactly one `status="pass"` `CheckResult`, never an empty list | N/A |
| Lint issues present | Generated code missing an import | `validation_checks` contains one `fail`-status `CheckResult` per missing-import `LintIssue`, plus one `compilation` `CheckResult` | N/A |

</frozen-after-approval>

## Code Map

- `src/multi_agent_mobile_ui_assistant/ui_generator.py:17` -- add `import operator` (needed for the `trace` reducer).
- `src/multi_agent_mobile_ui_assistant/ui_generator.py:25-42` (`UIGeneratorState`) -- add `trace: Annotated[list, operator.add]`; new module-level `class TraceStep(TypedDict)` and `class CheckResult(TypedDict)` near the top of the file, before `UIGeneratorState`.
- `src/multi_agent_mobile_ui_assistant/ui_generator.py:49-396` (`ui_generator_agent`, return at 392-396) -- append one `TraceStep` (e.g. summary = generated/regenerated, detail = code length or retry context).
- `src/multi_agent_mobile_ui_assistant/ui_generator.py:482-516` (`accessibility_reviewer_agent`) -- rework the `issues` list (lines 490-506) to build `CheckResult` objects per the Always rules; append a `TraceStep` in the return (512-516).
- `src/multi_agent_mobile_ui_assistant/ui_generator.py:523-562` (`ui_reviewer_agent`) -- same rework for `issues` (531-552); append a `TraceStep` in the return (558-562).
- `src/multi_agent_mobile_ui_assistant/ui_generator.py:569-616` (`output_node`) -- change the two `for issue in ...` loops (593, 603) to read `.message` (or `["message"]`) off each `CheckResult`; append a final `TraceStep` in the return (612-616).
- `src/multi_agent_mobile_ui_assistant/ui_generator.py:626-701` (`validator_node`) -- map `lint_issues` + `compilation_result` into `validation_checks` (new key in the return dict at 693-701); append a `TraceStep` covering both the pass-through-skip return (646) and the full-check return.
- `src/multi_agent_mobile_ui_assistant/android_tools_mcp.py:16-30` -- `LintIssue{severity,message,line,suggestion}` / `CompilationResult{success,errors,warnings}` -- read-only, source fields for the `validation_checks` mapping.
- `tests/test_ui_generator.py:149-195` (`TestAccessibilityReviewerAgent`), `:198-246` (`TestUIReviewerAgent`) -- update string-indexing assertions (e.g. `any("contentDescription" in issue ...)`) to read `issue["message"]`/`.message`.
- `tests/test_ui_generator.py:249-317` (`TestOutputNode`) -- update fixtures feeding plain strings into `output_node` to feed `CheckResult` objects instead.
- `tests/test_ui_generator.py:377-410` (`test_ui_generator_state_structure`) -- add `"trace": []` to the literal state dict and its assertions.

## Tasks & Acceptance

**Execution:**
- [ ] `ui_generator.py` -- add `TraceStep`/`CheckResult` TypedDicts + `trace` state field with `operator.add` reducer -- gives every node a shared, accumulating trace surface (AD-4)
- [ ] `ui_generator.py` -- `accessibility_reviewer_agent`/`ui_reviewer_agent` emit `CheckResult` lists instead of prose, one TraceStep each -- ends the "Good: ..." mixed-prose ambiguity (AD-3)
- [ ] `ui_generator.py` -- `validator_node` emits `validation_checks: list[CheckResult]` from `lint_issues`/`compilation_result`, one TraceStep each branch -- makes validator's checks structurally consistent with the other two reviewers (AD-3)
- [ ] `ui_generator.py` -- `ui_generator_agent`/`output_node` append their own TraceStep -- completes one-entry-per-executed-node coverage (CAP-2)
- [ ] `output_node` -- render `CheckResult.message` under the existing prose banners -- keeps `streamlit_interface.py`'s current parsing alive until story 3
- [ ] `tests/test_ui_generator.py` -- rework assertions on `accessibility_issues`/`design_issues`/`output_node` fixtures for the new `CheckResult` shape; add trace-accumulation and empty-findings-fallback tests

**Acceptance Criteria:**
- Given a full run with `validate_code=False`, when it completes, then `state["trace"]` has exactly one entry per node actually executed, in execution order.
- Given a run whose validator retries once, when it completes, then `trace` shows two `ui_generator` and two `validator` entries (no dropped or duplicated unrelated entries).
- Given generated code with zero accessibility findings, when `accessibility_reviewer_agent` runs, then `accessibility_issues` is a non-empty list of `CheckResult` with `status="pass"`.
- Given generated code with a missing import, when `validator_node` runs with `validate_code=True`, then `validation_checks` contains a `status="fail"` `CheckResult` for that lint issue.

## Design Notes

`TraceStep`/`CheckResult` as TypedDicts (not dataclasses) keeps them plain-dict-shaped like the rest of `UIGeneratorState`'s node returns, and JSON-friendly for story 3's eventual trace-panel rendering:

```python
class TraceStep(TypedDict):
    node: str
    summary: str
    detail: str

class CheckResult(TypedDict):
    check: str
    status: Literal["pass", "fail", "warn"]
    message: str
```

`trace` accumulates the same way `messages` already does — mirror the existing `Annotated[list, add_messages]` pattern with `Annotated[list, operator.add]`, and each node returns only its own new step(s) wrapped in a list.

## Verification

**Commands:**
- `uv run pytest tests/test_ui_generator.py -v` -- expected: all tests pass, including reworked reviewer/output tests and new trace/CheckResult tests.
- `uv run pytest tests/ -v --ignore=tests/test_mcp_tools.py` -- expected: full suite passes (the `test_mcp_tools.py` GitHub-network flake is pre-existing and unrelated, tracked in `deferred-work.md`).
