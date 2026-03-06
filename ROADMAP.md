# AI-Researcher Roadmap (Prioritized)

This roadmap focuses on reliability, reproducibility, and safety first, then
productization and UX.

## P0 - Reliability and Guardrails (Start Here)
- Add minimal automated tests for:
  - Benchmark instance schema validation.
  - MetaChain tool call handling (happy-path).
  - Log parsing in the web UI.
- Add runtime validation for agent outputs (structured JSON where required).
- Add explicit error messages for missing API keys and invalid task instances.
- Introduce a dry-run mode that skips external API calls and Docker.

## P1 - Reproducibility and Execution
- Standardize environment checks (Docker, GPU, browser tools).
- Ensure dataset setup is deterministic and logged.
- Store run metadata (model, prompts, commit hash, dataset) in a single JSON.

## P2 - Productization and Safety
- Add a high-level architecture doc with the end-to-end flow.
- Add schema-based specs for all agent inputs/outputs.
- Restrict web UI access to .env editing behind a warning gate.

## P3 - UX and Extensibility
- Add a guided CLI wizard for running tasks.
- Expand benchmark tools with a “preview task” command.
- Provide a plugin guide for new tools/agents.

## Current Sprint (In Progress)
- Add a benchmark instance schema test.
- Publish this roadmap in-repo.

- Draft a full rewrite plan for project/topic UX, metadata tagging, task pipelines, and vector organization (`RESEARCH_INTERFACE_REWRITE_PLAN.md`).
