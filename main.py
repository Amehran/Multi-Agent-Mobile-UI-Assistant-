"""CLI Entrypoint for the Multi-Agent Mobile UI Assistant."""

from src.multi_agent_mobile_ui_assistant import generate_ui_from_description


def main():
    """Run the CLI application."""
    print("=" * 70)
    print("Multi-Agent Mobile UI Assistant")
    print("Jetpack Compose Code Generator (CLI Mode)")
    print("=" * 70)
    print()

    user_input = input("Describe the UI you want to create (or press Enter for demo): ").strip()

    if not user_input:
        demo_prompt = "Create a login screen with an app logo, email field, password field with visibility toggle, and sign-in button"
        print(f"\nRunning with demo prompt: '{demo_prompt}'\n")
        output = generate_ui_from_description(demo_prompt)
        print(output)
    else:
        output = generate_ui_from_description(user_input)
        print(output)


if __name__ == "__main__":
    main()
