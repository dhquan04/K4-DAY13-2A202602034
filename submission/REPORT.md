# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm:
- Repository URL:
- Commit SHA cuối:
- Thành viên và vai trò:

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`:
- Tổng số traces:
- Số PII leak còn lại:
- Link/đường dẫn dashboard:

## 3. Logging và tracing

- Evidence correlation ID:
- Evidence PII redaction:
- Evidence trace waterfall:
- Giải thích một span đáng chú ý:

## 4. Prompt versioning

- Prompt name:
- Version/label baseline:
- Version/label candidate:
- Trace ID của mỗi version:
- Bằng chứng đổi label hoặc rollback:

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`: `HỢP LỆ: 6/6 panel có trong dashboard contract.`
- Evidence dashboard: `submission/evidence/dashboard-baseline.png` và `submission/evidence/dashboard-validator.txt`
- SLO đã chọn và lý do:
  - `latency_p95_ms`: Objective <= 3000ms (Target 99.5%) - Đảm bảo trải nghiệm tương tác trực tiếp không bị trễ.
  - `error_rate_pct`: Objective <= 2% (Target 99.0%) - Duy trì độ tin cậy và sẵn sàng của API.
  - `window_cost_usd`: Objective <= $2.50 trong cửa sổ 60 phút (`measurement_window: 60m`) - Quản lý ngân sách token LLM khớp với panel Cost trên Dashboard.
  - `quality_score_avg`: Objective >= 0.75 (Target 95.0%) - Đảm bảo chất lượng câu trả lời từ RAG & FakeLLM.
- Alert rules và runbook: 3 quy tắc cảnh báo symptom-based được khai báo tại `config/alert_rules.yaml` (`HighLatencyP95`, `HighErrorRate`, `DegradedResponseQuality`) kết nối trực tiếp với tài liệu hướng dẫn khắc phục sự cố tại `docs/alerts.md`.

## 6. Điều tra challenge

- Challenge ID:
- Triệu chứng từ metrics:
- Trace ID liên quan:
- Log line/correlation ID liên quan:
- Root cause:
- Fix action:
- Preventive measure:

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| | | | |
