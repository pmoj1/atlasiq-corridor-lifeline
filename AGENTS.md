# AtlasIQ project instructions

AtlasIQ is being built by a solo founder with AI assistance. Read README.md and agents/STATUS.md before project work. Follow the user's current instructions over this file. Do not invent product requirements or claim the founder has approved a suggested roadmap.

## Agent coordination

The team is in preparation mode by default. A generic “start” or “continue” activates agent setup only. Do not implement backlog features, alter product code, collect live data, or deploy anything unless the founder explicitly requests product development. When the user explicitly requests an AtlasIQ product build and collaboration tools are available, use a lead coordinator and delegate substantial independent tasks to specialists defined in agents/roles/. Keep at most three specialists active alongside the lead, subject to the environment's limit. Small tasks stay with the lead. If delegation is unavailable, follow the same roles sequentially and disclose that limitation. These files define reusable instructions; they do not create persistent running agents.

Read the relevant role file before assignment. Assign a concrete goal, allowed files, expected output and acceptance criteria. Only one agent may edit a file at a time. Specialists report to the lead and do not create further agents. The lead integrates changes and requests independent review before declaring a substantial feature ready.

## Working agreement

- Complete authorized local implementation and verification without repeated permission questions. Ask only for missing decisions that materially block the work.
- Keep the founder informed in plain language; explain what works, what was checked and what remains unresolved.
- Inspect actual code and current source evidence. Distinguish observed facts, assumptions and proposed changes.
- Do not contact people, send alerts, buy services or publish changes unless the user authorizes the action. Prepare concrete reviewable deployment artifacts first.
- Never store credentials in project files. Use environment variables and keep secrets out of logs.
- Preserve existing user files and changes. This directory initially has no Git repository; do not assume branches or worktrees are available.
- Update agents/STATUS.md after each completed work session. Record significant choices in agents/DECISIONS.md and keep task status accurate.

## Corridor integrity

This prototype produces an explainable rule score, not a calibrated probability or a demonstrated prediction of closure. Historical demo weather is illustrative. Missing or stale data must remain visible; never turn a gap into an all-clear. Keep timestamps, attribution and source provenance. Do not refresh verification timestamps merely on fetch. Preserve manually verified rail status until a verified replacement exists. Check data permissions before commercial deployment. README.md describes known source and coverage limitations.

## Verification

Use the project's available Python interpreter. If system Python fails on this Mac, the README documents a bundled interpreter. Run `python -m unittest discover -s tests -v` for behavioral changes and `python -m corridor_lifeline demo` for affected end-to-end output. Use a temporary output directory for verification when practical. Test meaningful failures and stale-data behavior for adapter/scoring changes. Report commands and actual results; never claim a check ran when it did not. Documentation-only edits need link and consistency checks, not new product tests.
