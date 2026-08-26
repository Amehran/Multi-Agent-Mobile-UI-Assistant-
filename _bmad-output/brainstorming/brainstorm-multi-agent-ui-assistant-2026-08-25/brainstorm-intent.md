# Brainstorm Intent: Multi-Agent Mobile UI Assistant

## Project / Purpose
A portfolio demo proving agentic AI design skill: a LangGraph multi-agent pipeline (Intent Parser -> Layout Planner -> UI Generator -> Lint/Gradle validation -> Accessibility/Design review) that turns a natural-language UI request into working Android Compose/Kotlin code, with visible self-checking and recovery — not just a prompt-chaining demo.

## Target Audience
Dual audience:
- Recruiter doing a 30-second skim (needs an immediately legible result/verdict)
- Engineer or hiring manager reading the orchestration code (needs to see real agent reasoning, checks, and recovery logic)

## Core Job to Be Done
Prove the ability to design agents that self-check and recover from mistakes — not just chain prompts together. The demo's job is to make this self-correction visible and credible, not to showcase UI-generation breadth.

## Inputs
Natural-language UI description, optionally mixing hard requirements with fuzzy style cues, e.g.:
> A login screen with email/password fields and a submit button, modern and trustworthy, fintech-like.

This forces genuine interpretation (concrete fields/buttons vs. subjective style language), not just template filling.

Should-have input path: Figma input via MCP.

## Outputs
Full bundle, not just code:
- Compose/Kotlin UI code
- Agent trace panel (shows pipeline steps/reasoning)
- Visual (HTML) preview
- Self-review verdict: accessibility/design pass-fail summary

## Requirements (MoSCoW)

**Must**
- NL-to-Compose core generation loop
- Agent trace panel
- Self-review verdict (accessibility/design pass-fail)

**Should**
- HTML visual preview
- Figma input via MCP
- Streamlit chat-based refinement

**Could**
- Fuzzy-style sample prompts (to demonstrate interpretation)
- Subtle auto-fix-on-error surfaced in the trace

**Won't**
- Staged "break it live" theatrics
- New input modalities beyond NL text / Figma

## Key Insight / Guiding Principle
The JTBD (prove self-correcting agents) and the "keep it simple" constraint converge on one move: expose the pipeline's existing agent trace and self-review — don't build new machinery to impress. When in doubt on scope, favor making existing self-correction visible over adding new capabilities.
