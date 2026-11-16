# Historical fixture provenance

These are two manually curated historical **rail event snapshots**, not a reconstruction of the full event timeline. Source facts were checked on 21 September 2026. Both demos include deliberately illustrative BOM-shaped weather and warning payloads to exercise the adapters offline; none of those payloads is an archived BOM record. Do not use these fixtures to claim measured warning lead time, predictive accuracy or a validated historical backtest.

| Fixture | Sourced historical fact | Scenario assumptions |
| --- | --- | --- |
| 2022 | ARTC's 15 February update reports resumed operations following a 24-day repair effort after the 21–23 January floods. | 08:00 UTC replay clock; 0 mm illustrative rain and an empty illustrative warning feed on the reopening day. |
| 2024 | ARTC's 27 March update announces a planned reopening between Kalgoorlie and Rawlinna at noon WA time on Easter Saturday, 30 March. The fixture therefore retains closed status on 27 March. | 08:00 UTC replay clock; 50 mm illustrative rain and a synthetic Rawlinna flood warning. |

Sources:

- [ARTC, South Australia flooding and track closure, 15 February 2022](https://www.artc.com.au/2022/02/15/south-australia-flooding-and-track-closure-update/)
- [ARTC, Western Australia flooding, 27 March 2024](https://www.artc.com.au/2024/03/27/latest-news-2/)

The planning PDF's July 2022 date conflicts with ARTC's January–February account. The prototype uses ARTC's dates and leaves the original PDF unchanged. The 2024 source announces reopening on Easter Saturday; the fixture does not claim reopening occurred later than Easter or treat that announcement as confirmation of a future event.

Each `config.json` includes `event_facts` with source URLs and a `fixture_note`, copied into demo output. Rail summaries paraphrase the cited announcements. Intraday observation times are chosen replay clocks and are not recovered publication timestamps. The 2022 retrospective rainfall figure in event facts is regional, not a station measurement or a scoring input.

To develop a real backtest, obtain archived station measurements and geographically relevant issued warnings, retain their original publication/availability times, and add pre-closure and recovery sequences. Evaluate out-of-sample events before making lead-time claims.
