"""Main entry point for the Multi-Agent Mobile UI Assistant."""

from src.multi_agent_mobile_ui_assistant.ui_generator import generate_ui_from_description


def main():
    """Run the main application."""
    print("=" * 70)
    print("Multi-Agent Mobile UI Assistant")
    print("Jetpack Compose Code Generator")
    print("=" * 70)
    print()
    
    # Example usage
    user_input = input("Describe the UI you want to create (or press Enter for demo): ").strip()
    
    if not user_input:
        # Run demo if no input provided
        from src.multi_agent_mobile_ui_assistant.ui_generator import run_demo
        run_demo()
    else:
        # Generate UI from user input
        generate_ui_from_description(user_input)


if __name__ == "__main__":
    main()
