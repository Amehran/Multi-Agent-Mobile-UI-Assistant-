---
title: 'Streamlit trace panel and verdict rendering'
type: 'feature'
created: '2026-08-26'
status: 'done'
review_loop_iteration: 0
context: []
baseline_commit: '210b5464e26d2172bd9c5d892fae7104f9633a0c'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `state["trace"]` and the `CheckResult` lists (`accessibility_issues`, `design_issues`, `validation_checks`) added by stories 1-2 never reach `streamlit_interface.py`. The UI still scrapes `output_node`'s prose banners via `extract_section`, and the Validation Report tab keys an ad hoc emoji off raw `LintIssue.severity`, not `CheckResult.status` — CAP-2/CAP-3 aren't demoable.
**Approach:** Decouple `generate_ui_from_description`'s structured-return path from `validate` so it always carries `trace`/`CheckResult` lists; have the initial-generation flow request it unconditionally; add a generic status-driven renderer (`pass|fail|warn` → `st.success|warning|error`, no message-text sniffing) for verdicts and a new Trace tab, retiring `extract_section` and the dead `auto_fixes` block. Scope is the initial-generation flow (`generate_initial_ui`) only — `refine_ui`'s own prose-review generation is a separate, deferred item (`deferred-work.md`).

## Boundaries & Constraints

**Always:**
- `generate_ui_from_description` (`ui_generator.py:905-1009`): change branch A's guard from `if validate and return_report:` to `if return_report and not multi_file:`; its returned dict gains `trace`, `accessibility_issues`, `design_issues`, `validation_checks` (straight off final graph state); `validation_report` key present (current shape, unchanged) only when `validate` was true, else `None`. The `not multi_file` guard preserves multi_file's existing dict-of-files contract untouched.
- `streamlit_interface.py` `generate_initial_ui` (175-224): call with `return_report=True` unconditionally (drop `and validate`); read `trace`/`accessibility_issues`/`design_issues`/`validation_checks` off the returned dict into session state (`current_trace`, and `current_accessibility`/`current_design` now holding `CheckResult` lists instead of prose strings). Reset all four to empty whenever the multi_file or Figma path is taken (neither produces them).
- New reusable renderer functions in `streamlit_interface.py`: one for `list[CheckResult]` (icon+message per item, `status` ∈ pass/warn/fail → `st.success`/`st.warning`/`st.error`, zero string inspection), one for `list[TraceStep]` (one line per step: `node` + `summary`, `detail` in an `st.expander` or `st.caption`).
- Replace the "📋 Reviews" columns (834-844) and the Validation Report tab's lint block (796-807) + dead `auto_fixes` block (824-829, tracked in `deferred-work.md`) with the generic `CheckResult` renderer, fed `accessibility_issues`/`design_issues`/`validation_checks` respectively.
- Add a "🔎 Trace" tab to the existing conditional-tab list (754-758 pattern) whenever `current_trace` is non-empty, rendered with the new trace renderer.
- History entries appended by `generate_initial_ui` (210-219): rename `accessibility`/`design` fields to hold the `CheckResult` lists; History tab (852-867) renders them with the same generic renderer.
- Remove `extract_section` (110-131) and its two call sites (199-200) once nothing depends on them.

**Ask First:** None.

**Never:**
- Do not modify `refine_ui` (230-362) at all — its prose-based review generation and its own `history.append` (348-356) stay exactly as-is; it is a separate, already-deferred item. Its history entries keep the old `accessibility`/`design` prose-string fields; the History tab renderer must handle both shapes (string → render as today via `st.markdown`, list → render via the new generic renderer).
- Do not touch `main.py` or change `validation_report`'s own field names/shape (locked by story 1).
- Do not fix the pre-existing multi_file+`return_report` ordering gap tracked in `deferred-work.md` — the `not multi_file` guard above keeps this story from making it worse, not better.
- Do not add new external dependencies or an `AppTest` harness (no precedent in this repo).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Generate, validate off | `validate=False` | Trace tab shows one entry per executed node; Reviews render generically; no Validation Report tab | N/A |
| Generate, validate on, passes | `validate=True` | Same, plus Validation Report tab renders `validation_checks` generically | N/A |
| Generate, validate on, fails once then passes | `validate=True`, code fails first attempt | Trace tab shows 2 `ui_generator`/2 `validator` entries; Validation Report shows checks from both attempts | N/A |
| Multi-file or Figma generation | `multi_file=True` or Figma import | No Trace tab, no Validation Report tab, Reviews empty (session state reset) | N/A |
| History includes an old refine-produced entry (prose strings) alongside new list-based entries | Mixed history after this story ships | History tab renders each entry correctly regardless of whether its accessibility/design field is a string or a `CheckResult` list | N/A |

</frozen-after-approval>

## Code Map

- `src/multi_agent_mobile_ui_assistant/ui_generator.py:905-1009` (`generate_ui_from_description`) -- branch A guard/dict at 975-998; branch B (multi_file) at 1001-1004 must stay reachable (hence the `not multi_file` guard).
- `src/multi_agent_mobile_ui_assistant/streamlit_interface.py:110-131` -- `extract_section` -- remove once call sites 199-200 are gone.
- `src/multi_agent_mobile_ui_assistant/streamlit_interface.py:175-224` (`generate_initial_ui`) -- call site + session-state population + history append (210-219) to rework.
- `src/multi_agent_mobile_ui_assistant/streamlit_interface.py:754-758` -- conditional tab list, add Trace tab here.
- `src/multi_agent_mobile_ui_assistant/streamlit_interface.py:788-829` -- Validation Report tab's lint block (796-807) and dead auto_fixes block (824-829, see `_bmad-output/implementation-artifacts/deferred-work.md`).
- `src/multi_agent_mobile_ui_assistant/streamlit_interface.py:834-844` -- Reviews columns.
- `src/multi_agent_mobile_ui_assistant/streamlit_interface.py:848-869` -- History tab rendering -- must branch on `isinstance(item['accessibility'], list)` vs `str` since `refine_ui`'s untouched entries stay string-shaped.
- `src/multi_agent_mobile_ui_assistant/streamlit_interface.py:230-362` (`refine_ui`) -- read-only reference point; do not modify (Never).
- `tests/test_streamlit_interface.py:51-74` -- `extract_section` tests, remove alongside the function.

## Tasks & Acceptance

**Execution:**
- [ ] `ui_generator.py` -- decouple branch A from `validate`, guard with `not multi_file`, add `trace`/`accessibility_issues`/`design_issues`/`validation_checks` to its return dict -- exposes stories 1-2's structured state (CAP-2/CAP-3)
- [ ] `streamlit_interface.py` -- `generate_initial_ui` requests the report unconditionally, populates new session-state keys, resets them on multi_file/Figma paths -- single source of trace/verdict data for the flow this story covers
- [ ] `streamlit_interface.py` -- add generic `CheckResult`/`TraceStep` renderer helpers -- one status-generic rendering path, no string-sniffing (CAP-3)
- [ ] `streamlit_interface.py` -- wire the renderers into Reviews columns, Validation Report tab, and a new Trace tab; delete the dead `auto_fixes` block and `extract_section` -- retires prose-based rendering for the generation flow
- [ ] `streamlit_interface.py` -- History append site (210-219) uses the renamed `CheckResult`-list fields; History tab rendering branches on string-vs-list so `refine_ui`'s untouched entries still render
- [ ] `tests/test_streamlit_interface.py` -- remove `extract_section` tests; add tests for the new renderer helpers and for `generate_ui_from_description`'s decoupled branch-A guard

**Acceptance Criteria:**
- Given `validate=False`, when a UI is generated, then the Trace tab shows exactly one entry per node actually executed, and Reviews render via status icons with no prose banner text visible anywhere.
- Given `validate=True` and code that fails once then passes, when generation completes, then the Validation Report tab shows `CheckResult`s from both attempts.
- Given `multi_file=True`, when generation completes, then no Trace or Validation Report tab appears and `output['code']` is still the multi-file dict (unaffected by the branch-A change).
- Given history containing both an old string-shaped entry and a new list-shaped entry, when the History tab renders, then both display without error.

## Design Notes

Generic verdict rendering, keyed only on `status`:

```python
def render_check_results(title, checks):
    st.subheader(title)
    if not checks:
        st.info("No checks recorded.")
        return
    for c in checks:
        icon_fn = {"pass": st.success, "warn": st.warning, "fail": st.error}[c["status"]]
        icon_fn(c["message"])
```

Trace rendering mirrors this shape (`node` + `summary` line, `detail` in a nested `st.caption` or `st.expander`) — same "generic off the structured field" principle, no reconstruction from console output (AD-4).

History rendering needs one small branch for the transition period: `if isinstance(item["accessibility"], list): render_check_results(...) else: st.markdown(item["accessibility"])` — this is temporary scaffolding that goes away once the deferred `refine_ui` item lands and every history entry is list-shaped.

## Verification

**Commands:**
- `uv run pytest tests/test_ui_generator.py -v` -- expected: all tests pass, including a new test for the decoupled branch-A guard (`return_report=True, validate=False` now returns the structured dict; `multi_file=True, return_report=True` still returns the multi-file dict).
- `uv run pytest tests/test_streamlit_interface.py -v` -- expected: all tests pass, including new renderer-helper tests; no `extract_section` tests remain.
- `uv run pytest tests/ -v --ignore=tests/test_mcp_tools.py` -- expected: full suite passes.

**Manual checks:**
- Launch the Streamlit app, generate a UI with validation on and one with it off, and visually confirm: the Trace tab lists nodes in execution order, Reviews/Validation Report render colored status icons (no bullet-prose), and History reflects the same structured data.
