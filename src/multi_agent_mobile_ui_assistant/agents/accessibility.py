"""
Accessibility Reviewer Agent.

Validates Compose UI for accessibility standards:
- Image contentDescription
- Minimum touch target sizes (48dp)
- Semantic content for screen readers
"""

from typing import Dict, Any, List
from ..core.state import UIGeneratorState


def accessibility_reviewer_agent(state: UIGeneratorState) -> Dict[str, Any]:
    """
    Accessibility Reviewer Agent: Audits code against Android accessibility guidelines.

    Args:
        state: Current workflow state

    Returns:
        Updated state dictionary with accessibility review notes
    """
    generated_code = state.get("generated_code", "")
    print("\n[Accessibility Reviewer] Checking accessibility compliance...")

    issues: List[str] = []

    # Check content descriptions for Image / Icon
    if "Image(" in generated_code and "contentDescription" not in generated_code:
        issues.append("Missing contentDescription for Image components")

    if "Icon(" in generated_code and "contentDescription" not in generated_code:
        issues.append("Missing contentDescription for Icon components")

    # Check touch target sizes for buttons
    if "Button(" in generated_code or "IconButton(" in generated_code:
        if "48.dp" not in generated_code and "size(" not in generated_code:
            issues.append("Ensure interactive elements meet minimum 48dp touch target size")

    # Check for text elements
    if "Text(" in generated_code:
        issues.append("Consider semantic labels for screen readers where appropriate")

    if not issues:
        issues.append("No major accessibility issues found")

    print(f"[Accessibility Reviewer] Found {len(issues)} items to review")
    for issue in issues:
        print(f"  - {issue}")

    return {
        "messages": [{"role": "assistant", "content": "Accessibility review complete"}],
        "accessibility_issues": issues,
        "current_step": "accessibility_reviewed",
    }
