---
title: Multi-Agent Mobile UI Assistant
status: final
created: 2026-08-25
updated: 2026-08-25
---

# Multi-Agent Mobile UI Assistant — PRD

## Overview

A portfolio demo proving agentic AI design skill. An existing LangGraph multi-agent pipeline (Intent Parser → Layout Planner → UI Generator → Lint/Gradle validation → Accessibility/Design review) turns a natural-language UI request into working Android Jetpack Compose/Kotlin code. The point of the demo is not code generation breadth — it's making the pipeline's self-checking and recovery **visible and credible**.

Public GitHub repo. Solo project, no team or deadline pressure — scope stays lean.

## Target Users

- **Recruiter** — 30-second skim; needs an immediately legible result.
- **Engineer / hiring manager** — reads the orchestration code and demo output; needs to see real agent reasoning, checks, and recovery, not just a polished UI.

## Core Job to Be Done

Prove the ability to design agents that **self-check and recover from mistakes**, not just chain prompts. Every scope decision should favor making existing self-correction visible over adding new capabilities.

## Goals & Success Metrics

- 3 curated demo prompts each run end-to-end in a single pass, producing: compiling Compose code, a populated agent-trace panel, and a pass/fail self-review verdict — reproducibly, without manual intervention.
- **Counter-metric:** don't over-fit to the curated prompts — at least one off-script/ad-hoc prompt should also complete without breaking the pipeline, so the demo isn't visibly rehearsed.

## Demo Flow

1. User enters a natural-language UI description (may mix concrete requirements with a fuzzy style cue — see FR-7).
2. Pipeline runs; the trace panel populates live as each agent (Intent Parser, Layout Planner, UI Generator, Validator, Reviewers) completes its step.
3. Final output bundle renders together: Compose/Kotlin code, HTML preview, and self-review verdict.
4. User may refine conversationally (Streamlit chat) and watch the bundle update.

## Functional Requirements

**Must**
- **FR-1**: Accept a natural-language UI description and generate valid Jetpack Compose/Kotlin code.
- **FR-2**: Display an agent-trace panel showing each pipeline stage's decision/output.
- **FR-3**: Run an automated self-review (accessibility + Material 3 compliance) and surface a pass/fail verdict per check.

**Should**
- **FR-4**: Render a visual HTML preview of the generated UI alongside the code.
- **FR-5**: Accept a Figma file/frame reference via the existing Figma MCP integration as an alternative input.
- **FR-6**: Support iterative refinement via the Streamlit chat interface, applying incremental edits to prior output.

**Could**
- **FR-7**: Ship curated sample prompts that mix concrete requirements with subjective style language, to demonstrate genuine interpretation.
- **FR-8**: When validation fails, surface the specific error and the corrective action taken in the trace panel (auto-fix-on-error), rendered plainly rather than staged.

## Non-Functional Requirements

- **Reliability**: curated demo prompts must complete end-to-end without manual intervention (see Success Metrics).
- **No new external dependencies**: build on the existing stack (LangGraph, Streamlit, Ollama/OpenAI providers, Figma MCP, Android Lint/Gradle MCP) — locked constraint, not an open decision.
- **Secrets hygiene**: API keys/tokens stay in `.env`, never committed — repo is public.
- **Latency**: generation loop must feel live/interactive for a demo (not a batch job with a long silent wait).

## Out of Scope

- Staged "break it live" failure theatrics.
- New input modalities beyond NL text and Figma.
- Production-grade hardening (auth, multi-user support, persistent storage beyond session).

## Guiding Principle

The JTBD (prove self-correcting agents) and the lean-scope constraint converge on one move: **expose what the pipeline already does — don't build new machinery to impress.**

## Open Questions

- Exact content (wording) of the 3 curated demo prompts — decide during implementation/demo scripting.
