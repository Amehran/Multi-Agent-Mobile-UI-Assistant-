"""
Visual Layout Preview Generator.

Renders an HTML-based structural mock visualization of the generated Jetpack Compose UI.
"""

import html
import re


def generate_preview_html(code: str) -> str:
    """
    Generate an XSS-safe HTML visual preview from Kotlin Compose code.

    Args:
        code: Kotlin Compose code string

    Returns:
        HTML snippet representing visual layout
    """
    if not code:
        return "<p style='color: #888; text-align: center;'>No code to preview</p>"

    colors = {
        "Icon": "#FF6B35",
        "Text": "#2196F3",
        "TextField": "#4CAF50",
        "Button": "#6200EE",
    }

    lines = code.split("\n")
    html_parts = [
        '<div style="font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif; padding: 16px; background: #f0f2f5; border-radius: 12px;">',
        '<div style="max-width: 420px; margin: 0 auto; background: white; padding: 24px; border-radius: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.08);">',
    ]

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Icon component
        if "Icon(" in stripped and "IconButton" not in stripped and "imageVector" in stripped:
            icon_name = "Icon"
            if "Icons.Default." in stripped:
                try:
                    icon_name = stripped.split("Icons.Default.")[1].split(",")[0].split(")")[0].strip()
                except Exception:
                    pass
            icon_emoji = "👤" if "Account" in icon_name or "Person" in icon_name else ("🔒" if "Lock" in icon_name else "✨")
            html_parts.append(
                f'<div style="margin: 12px 0; text-align: center;">'
                f'<div style="font-size: 2.2em;">{icon_emoji}</div>'
                f'<div style="font-size: 0.8em; color: #888; margin-top: 4px;">{html.escape(icon_name)}</div>'
                f'</div>'
            )

        # Spacer component
        elif "Spacer(" in stripped and "Modifier" in stripped:
            height = "16.dp"
            if ".height(" in stripped:
                try:
                    height = stripped.split(".height(")[1].split(")")[0]
                except Exception:
                    pass
            html_parts.append(
                f'<div style="margin: 4px 0; padding: 4px; background: #fafafa; border-radius: 4px; text-align: center;">'
                f'<span style="font-size: 0.7em; color: #bbb;">↕ Spacer ({html.escape(height)})</span>'
                f'</div>'
            )

        # Text component (standalone)
        elif "Text(" in stripped and "TextField" not in stripped and not any(x in line for x in ["Button", "label =", "placeholder ="]):
            text_val = ""
            m = re.search(r'text\s*=\s*"([^"]+)"', stripped) or re.search(r'Text\("([^"]+)"\)', stripped)
            if m:
                text_val = m.group(1)

            if text_val and text_val != "OR":
                is_headline = any("headline" in lines[j] or "title" in lines[j] for j in range(i, min(i + 3, len(lines))))
                f_size = "1.3em" if is_headline else "0.95em"
                f_weight = "bold" if is_headline else "normal"
                align = "center" if is_headline else "left"
                html_parts.append(
                    f'<div style="margin: 8px 0; font-size: {f_size}; font-weight: {f_weight}; text-align: {align}; color: #222;">'
                    f'{html.escape(text_val)}'
                    f'</div>'
                )

        # OutlinedTextField
        elif "OutlinedTextField(" in stripped:
            label = "Input"
            placeholder = ""
            lookahead = "\n".join(lines[i: min(i + 8, len(lines))])
            m_label = re.search(r'label\s*=\s*\{\s*Text\("([^"]+)"\)', lookahead)
            if m_label:
                label = m_label.group(1)
            m_ph = re.search(r'placeholder\s*=\s*\{\s*Text\("([^"]+)"\)', lookahead)
            if m_ph:
                placeholder = m_ph.group(1)

            html_parts.append(
                f'<div style="margin: 10px 0; padding: 10px 14px; border: 1.5px solid #ccc; border-radius: 8px; background: #fff;">'
                f'<div style="font-size: 0.72em; color: #666; font-weight: 500;">{html.escape(label)}</div>'
                f'<div style="font-size: 0.9em; color: #aaa; margin-top: 2px;">{html.escape(placeholder) or "Enter text..."}</div>'
                f'</div>'
            )

        # Button / OutlinedButton
        elif ("Button(" in stripped or "OutlinedButton(" in stripped) and "IconButton" not in stripped:
            btn_text = "Button"
            is_outlined = "OutlinedButton" in stripped
            lookahead = "\n".join(lines[i: min(i + 6, len(lines))])
            m_btn = re.search(r'Text\("([^"]+)"\)', lookahead)
            if m_btn:
                btn_text = m_btn.group(1)

            if is_outlined:
                html_parts.append(
                    f'<div style="margin: 12px 0; padding: 12px; border: 1.5px solid {colors["Button"]}; color: {colors["Button"]}; border-radius: 8px; text-align: center; font-weight: 600;">'
                    f'{html.escape(btn_text)}'
                    f'</div>'
                )
            else:
                html_parts.append(
                    f'<div style="margin: 12px 0; padding: 12px; background: {colors["Button"]}; color: white; border-radius: 8px; text-align: center; font-weight: 600; box-shadow: 0 2px 6px rgba(98,0,238,0.3);">'
                    f'{html.escape(btn_text)}'
                    f'</div>'
                )

        # Divider / OR
        elif "HorizontalDivider(" in stripped or "Divider(" in stripped:
            html_parts.append(
                '<div style="margin: 14px 0; display: flex; align-items: center; gap: 8px;">'
                '<div style="flex: 1; height: 1px; background: #e0e0e0;"></div>'
                '<span style="font-size: 0.75em; color: #999;">OR</span>'
                '<div style="flex: 1; height: 1px; background: #e0e0e0;"></div>'
                '</div>'
            )

    html_parts.append("</div></div>")
    return "\n".join(html_parts)
