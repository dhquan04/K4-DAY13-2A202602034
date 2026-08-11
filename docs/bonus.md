# Bonus: Cost Optimization, Audit Log, and Anomaly Automation

## Implemented controls

- `POST /cost-optimization/enable` enables an output-token cap. The cap is configured by `MAX_OUTPUT_TOKENS` (default `160`) and only applies when explicitly enabled.
- `data/audit.jsonl` records control-plane events only: `incident_enabled`, `incident_disabled`, and `config_changed`. The path is configured by `AUDIT_LOG_PATH`.
- `scripts/detect_anomalies.py` detects PII patterns and response latency exceeding `latency_p95_ms` from `config/slo.yaml`.

## Reproducible before/after measurement

With the API running from the repository root:

```powershell
python scripts/inject_incident.py --scenario cost_spike
python scripts/load_test.py --concurrency 5
python scripts/measure_cost.py --last 10 --label before | Tee-Object submission/evidence/bonus-cost-before.txt

Invoke-RestMethod -Method Post http://127.0.0.1:8000/cost-optimization/enable
python scripts/load_test.py --concurrency 5
python scripts/measure_cost.py --last 10 --label after | Tee-Object submission/evidence/bonus-cost-after.txt

python scripts/inject_incident.py --scenario cost_spike --disable
Invoke-RestMethod -Method Post http://127.0.0.1:8000/cost-optimization/disable
python scripts/detect_anomalies.py --fail-on-anomaly
```

Take dashboard screenshots after the `before` and `after` measurements and save them as `submission/evidence/bonus-cost-before.png` and `submission/evidence/bonus-cost-after.png`. The text files make the exact totals reproducible; the screenshots show the dashboard state.
