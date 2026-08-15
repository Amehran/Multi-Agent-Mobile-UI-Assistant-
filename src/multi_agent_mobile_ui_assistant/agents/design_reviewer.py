"""
Material 3 Design Reviewer Agent.

Evaluates Compose UI code against Material 3 design guidelines:
- Consistent theming (MaterialTheme.colorScheme, typography)
- Spacing hierarchy (padding, arrangement)
- Layout structure (Alignment, Arrangement)
"""

from typing import Dict, Any, List
from ..core.state import UIGeneratorState


def ui_reviewer_agent(state: UIGeneratorState) -> Dict[str, Any]:
    """
    UI Reviewer Agent: Audits code against Material 3 standards.

    Args:
        state: Current workflow state

    Returns:
        Updated state dictionary with design review notes
    """
    generated_code = state.get("generated_code", "")
    print("\n[UI Reviewer] Evaluating against Material 3 guidelines...")

    issues: List[str] = []

    # MaterialTheme compliance
    if "MaterialTheme" not in generated_code:
        issues.append("Consider using MaterialTheme tokens for consistent theming")
    else:
        issues.append("Good: Uses MaterialTheme tokens")

    # Spacing and Padding
    if "padding" in generated_code:
        issues.append("Good: Uses modifier padding for spacing hierarchy")
    else:
        issues.append("Consider adding padding to containers for visual hierarchy")

    # Container layout arrangement
    if "Arrangement" in generated_code:
        issues.append("Good: Uses Arrangement for element positioning")

    if not issues:
        issues.append("Code adheres to Material 3 design principles")

    print(f"[UI Reviewer] Found {len(issues)} design considerations")
    for issue in issues:
        print(f"  - {issue}")

    return {
        "messages": [{"role": "assistant", "content": "UI review complete"}],
        "design_issues": issues,
        "current_step": "ui_reviewed",
    }
