# Corridor Lifeline — coffee and demo brief

Prepared 13 October 2026 · Possible late-November 2026 coffee with Craig Jones of Perseus Mining · Founder review draft

Meeting timing and Craig’s role are unconfirmed. Perseus’s exposure to this corridor, operational needs and interest have not been established. This brief uses local project evidence; it is not company research or a proposal for an agreed pilot.

**Purpose:** learn whether clearer disruption information would help a mining operator make a specific supply decision, and what evidence would make it credible. Suggested format: 20-minute conversation, including a three-minute offline demo.

**Opening:** “I’m building AtlasIQ as a solo founder. Corridor Lifeline is an early local prototype that brings configured weather signals and manually verified rail status into an explainable summary and an email draft. I’d like to understand whether this solves a real operational problem for mining teams, and where it falls short.”

## Operational problem and fit to test

When freight conditions change, a team may need to reconcile weather warnings, operator updates and supply commitments before deciding whether to dispatch, check stock buffers or revise delivery expectations. Corridor Lifeline addresses the information-synthesis step: what changed, why the indicator moved, where the evidence came from and what still needs checking.

**Hypothesis, not a verified customer finding:** mining operations with corridor-dependent supplies could find this useful when disruption threatens critical deliveries. Ask Craig which routes and supplies actually matter before assuming the Australian east–west rail prototype fits Perseus. If it does not, use the discussion to test the workflow rather than promise coverage elsewhere.

## Three-minute demo: existing capabilities only

Use the saved [2024 draft](../output/demo/2024/alert.txt), [2024 evidence JSON](../output/demo/2024/latest.json) and [2022 draft](../output/demo/2022/alert.txt). These are local offline outputs, not current conditions. No browser dashboard or live fetch is needed.

| Time | Show | Say |
| --- | --- | --- |
| 0:00–0:25 | The `[DEMO]` label and replay timestamp in the 2024 draft | “This is a historical rail snapshot with illustrative weather and warnings. It demonstrates software behaviour, not advance-warning performance.” |
| 0:25–1:10 | CRITICAL 100/100, reasons and operator-check advice | “Rain contributes 25 points, the synthetic warning 30 and closed rail 100; the sum is capped at 100. Closure alone reaches 100. This does not mean a 100% probability.” |
| 1:10–1:55 | JSON `components`, `feeds`, `observed_at`, `health`, `sources`, `fixture_note` and `event_facts` | “The evidence and its limits remain inspectable. A future reopening announcement stays closed in this snapshot. ‘Complete for configured inputs’ does not mean the whole corridor is covered.” |
| 1:55–2:25 | Plain-language action and the saved `.eml` draft alongside it | “A person reviews this and checks with the operator. The prototype prepares drafts; it never sends email or checks an alternative road route.” |
| 2:25–3:00 | 2022 LOW 0/100 draft and its caution | “This separate reopening snapshot is not a recovery timeline or an all-clear. What decision, if any, would these summaries help your team make?” |

For a fresh offline rehearsal, run from the project root using the bundled interpreter:

```sh
/Users/a111/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m corridor_lifeline demo --out /tmp/atlasiq-coffee-rehearsal
```

Outputs appear under `/tmp/atlasiq-coffee-rehearsal/demo/{2022,2024}/`. Do not run `once` or `watch` for this meeting preparation.

## Creative material: optional context, clearly labelled

The [30-second captioned film](../creative/corridor-film-30s/exports/AtlasIQ-30s-captioned.mp4) is a short, muted-friendly opener. Introduce it as **an illustrative development concept** before playback, then switch to actual text/JSON outputs. Its interface and paperwork are not working product features; “Before the disruption” is a creative title, not demonstrated warning lead time.

The [one-minute captioned story](../creative/corridor-film-60s/exports/AtlasIQ-60s-captioned.mp4), “One shipment. One promise.”, is an optional longer conversation aid. Its dispatcher, imagery, screens and documents are fictional/illustrative; narration is synthetic. The [15-second explainer](../creative/corridor-explainer/README.md) is another concept option. Avoid playing all three. The website’s Detect / Alert / Prepare narrative distinguishes prototype detection from proposed subscriber delivery and paperwork support.

## Claim boundaries to keep beside the demo

- **Exists:** local Python adapters, transparent rule scoring, source/freshness details, visible information gaps, text and MIME email drafts, offline scenarios. It is deterministic software; an AI agent is not implemented.
- **Illustrative:** demo weather/warnings, replay intraday clocks and score thresholds. Historical rail facts have local provenance records, checked in September 2026; they were not reverified in this session. Neither scenario is a validated historical backtest.
- **Unverified:** relevance to Perseus, operator willingness to use it, savings, ROI, customer adoption, closure prediction and warning lead time. No commercial feed permission or current endpoint availability is established by this demo.
- **Planned/proposed, not available or newly approved:** subscriber alert delivery and emergency-paperwork support. No operational dashboard, permit drafting/submission, route optimisation or automatic regulatory approval exists in this prototype.
- **Coverage limits:** default weather configuration has only Kalgoorlie-Boulder; warning geography uses coarse text matching. Rain is since local 9 am, not rolling 24 hours. Stale/missing inputs remain gaps; low scores with gaps display UNKNOWN. Fetching does not renew rail verification. BOM RSS commercial permissions need review before commercial deployment.

## Focused questions for Craig

1. Which inbound routes and supplies are most exposed to disruption? Does this corridor matter to your operations at all?
2. In the last disruption you can discuss, what decision was delayed by incomplete or conflicting information, and who owned it?
3. What updates do logistics, procurement and site teams already receive? Where does manual reconciliation still happen?
4. How much usable notice would change a stock, dispatch or delivery decision? What false-alarm burden is acceptable?
5. What source authority, timestamp and geographic detail would you require? How should UNKNOWN information be presented?
6. Would the draft summary fit an existing workflow? What evidence would justify evaluating it further, and who would review that evidence?

**Close:** “The useful outcome for me is one real decision and the evidence needed to support it. I can use that to assess whether this direction is worth pursuing.” Record fit, decision owner, existing information sources and objections locally. Any subsequent data request, outreach or pilot remains a separate founder decision.

## Evidence and rehearsal record

Capability boundaries checked against [README](../README.md), [CLI](../corridor_lifeline/__main__.py), [scoring](../corridor_lifeline/engine.py), [draft generation](../corridor_lifeline/alerts.py), [fixture provenance](../fixtures/README.md), [website copy](../website/corridor-lifeline-copy.md) and the three creative READMEs. Creative playback/decoding was not rechecked in this session.

Offline command run on 13 October 2026: bundled Python `-m corridor_lifeline demo --out /tmp/atlasiq-coffee-demo-20261013`; exit 0, 2022 LOW 0/100 and 2024 CRITICAL 100/100, both complete for configured inputs. No live collection occurred. Documentation links and output consistency checked; product tests were not rerun because behaviour was unchanged.
