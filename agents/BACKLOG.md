# Proposed AtlasIQ task board

Only work on the task the founder activates. The launch prompt prepares the agents and activates no product task. All other tasks remain proposed until selected.

## W01 — Corridor Lifeline website narrative and project organisation

Status: local implementation completed; live publication pending access to the existing Netlify project.
Scope: Premium photographic redesign with animations, responsive layouts and accessible plan tabs. Rewrite public website narrative and metadata around Corridor Lifeline, retain only Jay-deane Huni as founder, and consolidate AtlasIQ materials in this linked project directory. Keep current prototype and proposed capabilities distinct. Website review and browser checks are recorded in agents/STATUS.md and website/verification/.
Product backlog A01–A05 remains unactivated.

## A01 — Show the existing result in a local dashboard

Status: pending — product development explicitly deferred by the founder.
Goal: Let the founder inspect corridor conditions without reading JSON.
Scope: Read existing latest.json output and display corridor, score, level, source timestamps, reasons and data gaps. Prefer a small solution compatible with the existing Python project; do not add an LLM dependency.
Acceptance: Offline demos render; absent/malformed output produces an understandable state; incomplete coverage and fixture provenance are prominent; stale output is visible using an explicit age policy; source text is safely rendered; instructions explain local launch. Existing tests pass and the reviewer checks the display against actual JSON. Never imply live monitoring from a historical demo.
Roles: Lead, Product, Builder, Reviewer. Data consulted for timestamp and provenance rules.

## A02 — Keep inspectable history

Status: proposed.
Goal: Retain observations and score changes with timestamps and provenance.
Acceptance: Retention and write behavior documented; interrupted writes handled; duplicate collection behavior explicit; no secrets retained; meaningful persistence tests pass.

## A03 — Improve rail-status collection

Status: proposed.
Goal: Reduce manual effort while preserving verified evidence.
Acceptance: Confirm available permitted sources first; link source announcements; separate extracted candidate status from verified status; preserve verification times and surface uncertainty. Do not assume a machine-readable operator API exists.

## A04 — Prepare a hosted pilot

Status: proposed.
Goal: Produce a reviewable hosting plan and runnable deployment artifacts.
Acceptance: Document costs, source permissions, configuration, scheduler ownership, health checks, access controls, backup and rollback; verify restart behavior. Publish only when instructed by the founder.

## A05 — Add a controlled alert workflow

Status: proposed.
Goal: Deliver actionable changes to explicitly configured recipients.
Acceptance: Define recipients and delivery authorization; handle deduplication, retries, cancellation and data gaps; test with a local sink before real delivery. No recipients or sending service assumed.


## C01 — Closure-review local demonstration
Status: implemented and verified22October2026. Explicit founder build authorisation.
Scope: sourced Yaoure2018 baseline, illustrative comparison, CSV engine, responsive branded charts/tables/evidence, review export and optional OpenAI explanation integration.
Verification:28 tests plus browser import/export and desktop/mobile checks; independent review passed. Live OpenAI call awaits founder local key/model configuration. Native arbitrary document ingestion and survey validation are unimplemented. See closure_review/README.md.


## C02 — Native XLSX mapping and cell lineage
Status: implemented/verified23October2026. User-authorised difficult-work upgrade.
Acceptance: sheet/header preview, explicit columns/row scope/exclusions, blockers for invalid/error/missing-cache inputs, stated-cost reconciliation, deterministic version comparison, source cells/file fingerprints and export.35tests pass plus independent review/browser workflow. Representative private closure-model validation and survey reconciliation remain unimplemented/unverified.

### A01 update — 23 October 2026
Local implementation complete following explicit corridor-build continuation request. Independent correctness review and38tests pass; browser visual QA remains unverified. Launch documented in README. Other A02–A05 tasks remain proposed.

### Corridor build activation — 25 October 2026
Founder explicitly requested the corridor system and location checks. A01 expanded and verified with location screening, source-refresh control, evidence, integrated supply scenario and exports. A02 implemented locally: SQLite distinct-payload retention1,000; UIlatest100. A03 retains manual verified rail bridge; automated verified collection unimplemented. A04/A05 hosting/delivered alerts remain unimplemented. New location scope is approximate geography screening, not surveyed track, mine connectivity or hazard intersection.49tests plus independent/browser verification; see STATUS and corridor_lifeline/verification/RESULTS.md.

### Real-context extension — 25 October 2026
Implemented direct USGS event layer with source evidence and location screening. Hosted World Monitor integration remains pending access and adapter implementation; do not call upstream reuse a WM integration.55tests and independent review passed.

7 November: local notice-desk interface and public WA roads, WA/SA warnings and ARTC news adapters integrated. DFES warning-layer verification and authoritative rail operations feed remain open.
