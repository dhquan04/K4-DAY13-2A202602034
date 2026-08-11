# Dashboard specification — Day 13 AI Observability

`config/dashboard.yaml` is the machine-validated contract. This document is the
runtime design used to build and review the dashboard. Keep the main view to the
six panels below; do not substitute Langfuse traces for the JSONL log data source.

## Global settings

- Default time range: last 60 minutes.
- Refresh: every 30 seconds.
- Source of truth: `data/logs.jsonl`.
- Every panel shows its unit and the threshold/SLO line from
  `config/dashboard.yaml`.
- The errors panel may display the live `/metrics.error_rate_pct` as a compact
  current-value card, but the dashboard time-series calculation remains based on
  log events so it is reproducible during incident investigation.

## Six-panel contract

| ID | Panel and visualization | Source/event fields | Calculation | Unit and threshold |
|---|---|---|---|---|
| `latency` | Line chart with P50, P95, P99 | `response_sent.latency_ms` | Percentiles over completed responses in each selected time bucket | ms; P95 <= 3000 |
| `traffic` | Request-per-minute line or bars | `request_received` | Count requests by one-minute bucket | requests/minute; >= 1 |
| `errors` | Error-rate line plus error-type breakdown | `request_received`, `request_failed.error_type` | `count(request_failed) / count(request_received) * 100`; group failures by `error_type` | percent; <= 2% |
| `cost` | Cost-per-minute line plus window total | `response_sent.cost_usd` | Sum by minute and sum over selected window | USD; total <= 2.5 |
| `tokens` | Input/output token comparison | `response_sent.tokens_in`, `response_sent.tokens_out` | Sum each field independently | tokens; each input/output total <= 50,000 |
| `quality` | Quality-score line or current-value card | `response_sent.quality_score` | Mean score in each selected time bucket | score 0–1; >= 0.75 |

## Error-rate consistency rule

The API increments `traffic` when it emits `request_received`; an unhandled
request failure increments `error_breakdown`. Therefore `/metrics.error_rate_pct`
uses the same formula as the `errors` panel:

```text
error_rate_pct = request_failed / request_received * 100
```

For a clean process, three successful requests and one failed request must show
`traffic = 4`, `error_breakdown = {"RuntimeError": 1}`, and
`error_rate_pct = 25.0` from `/metrics`.

## Runtime evidence checklist

1. Start from a fresh, PII-safe `data/logs.jsonl`, then run the baseline load test.
2. Capture the dashboard with the time range, six panel names, units, and threshold
   lines visible.
3. Enable `rag_slow`, run the same load test, and capture the increased P95 panel.
4. Record the affected time window, a matching trace ID, and its correlation ID in
   `submission/REPORT.md`; then disable the incident.
5. Run `python scripts/validate_dashboard.py` and save its successful output.

The dashboard is complete only when both the YAML validator and the runtime
evidence above are available.
