- source_spec: `_bmad-output/specs/spec-multi-agent-mobile-ui-assistant/stories/1-in-graph-validator-retry-loop.md`
  summary: `generate_ui_from_description(validate=True, return_report=True, multi_file=True)` returns the flat `{"code", "validation_report"}` dict and never reaches the multi-file parsing branch, silently dropping the multi-file breakdown.
  evidence: Confirmed via diff structure that the early-return-before-multi_file-check control flow is unchanged from before this story (pre-existing, not introduced by the validator/retry work); untested combination, surfaced incidentally by review.

- source_spec: `_bmad-output/specs/spec-multi-agent-mobile-ui-assistant/stories/1-in-graph-validator-retry-loop.md`
  summary: `streamlit_interface.py`'s "Auto-fixes Applied" panel reads `report['auto_fixes']`, a key `generate_ui_from_description`'s `validation_report` never populates (only `auto_fixed`, a bool) — permanently dead code.
  evidence: Confirmed via `git show HEAD:src/multi_agent_mobile_ui_assistant/ui_generator.py` that the `auto_fixed`-only key predates this story; pre-existing and unaffected by this diff.

- source_spec: `_bmad-output/specs/spec-multi-agent-mobile-ui-assistant/stories/1-in-graph-validator-retry-loop.md`
  summary: `tests/test_mcp_tools.py::TestGitHubMCP::test_search_compose_examples_returns_list_of_examples` intermittently hangs (real, unmocked `PyGithub`/network call in `GitHubMCP`), occasionally blocking a full unfiltered `uv run pytest tests/` run from completing.
  evidence: Reproduced twice as flaky (hangs when run as part of the full suite, passes when `tests/test_mcp_tools.py` is run alone); zero diff in `mcp_tools.py`/`test_mcp_tools.py` from this story, so pre-existing and out of this story's Code Map/scope. Fix direction: mock `GitHubMCP`/`PyGithub` in tests or add a request timeout.
