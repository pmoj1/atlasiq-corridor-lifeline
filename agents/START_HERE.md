# Your AtlasIQ agent team

Prepared on 8 October 2026. Status: standby.

This is a project-local instruction kit for Codex. There is nothing to install, no API key required for this kit, and no process running in the background. Role definitions become active when Codex reads them and assigns work. Agent calls consume the usage allowance of the environment running them. Always-on hosting is a separate future setup.

## Start when ready

Open this AtlasIQ folder in Codex and say:

> Activate my AtlasIQ agent team in preparation mode only. Validate the roles and coordination. Keep product development pending until I explicitly request it.

The same prompt is saved in agents/LAUNCH_PROMPT.txt.

## Roles

| Role | Work |
| --- | --- |
| Lead | Own the plan, assignments, integration and progress updates |
| Product | Turn the founder's priorities into a small usable release |
| Builder | Implement features and repair defects |
| Data | Check sources, freshness, coverage and evidence |
| Reviewer | Independently inspect correctness and run meaningful checks |
| Release | Prepare hosting, operations, recovery and deployment steps |

Six roles do not require six simultaneous agents. The lead selects only the roles needed for a task, with up to three specialists active at once. Specialists can be reused across tasks.

## Session handoff

STATUS.md records current reality. BACKLOG.md holds proposed work and acceptance criteria. DECISIONS.md records decisions and their reasons. Completed tasks must include changed files, verification evidence and remaining limitations.

To authorize product work later, say: “Build [specific feature] with my AtlasIQ agent team.” Generic start/continue messages only activate preparation. Your instructions override the suggested backlog.
