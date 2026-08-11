
# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm: ChickenFarmer
- Repository URL: https://github.com/dhquan04/K4-DAY13-2A202602034
- Commit SHA cuối: 7f52ee1e29391475298a4868b22bc7cf6b780d4a
- Thành viên và vai trò:
  1. Trịnh Hoàng Nam (2A202601376) - Role A: API & Middleware (Correlation ID, Exception Handlers)
  2. Đỗ Việt Tùng (2A202601876) - Role B: Security Engineer (PII Redaction, Regex Patterns)
  3. Đinh Hoàng Quân (2A202602034) - Role C: Metrics & Dashboard (Error Rate, Dashboard Contract 6 Panel)
  4. Hoàng Thanh Sơn (2A202601848) - Role D: SRE & Alerts Engineer (SLO, Alert Rules, Alert Runbook)
  5. Vũ Bảo Chinh (2A202601448) - Role E: QA & Chief Investigator (Sub-component Tracing RAG/LLM, Load test, Điều tra Challenge CP3 & Tổng hợp Báo cáo)

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: 100/100 (Pass 4/4 tiêu chí)
- Tổng số traces: 10+ traces (đã ghi nhận trên Langfuse Cloud)
- Số PII leak còn lại: 0
- Link/đường dẫn dashboard: /dashboard

## 3. Logging và tracing

- Evidence correlation ID: `req-35a4fc0c` (truyền xuyên suốt HTTP header `x-request-id` và structlog contextvars trong log `data/logs.jsonl`)
- Evidence PII redaction: Đã kiểm chứng scrub toàn bộ email `[REDACTED_EMAIL]`, SĐT `[REDACTED_PHONE_VN]`, thẻ `[REDACTED_CREDIT_CARD]` tại `submission/evidence/log-pii-redacted.txt`
- Evidence trace waterfall: Span `rag_retrieval` (Span) và `llm_generation` (Generation) ghi nhận đẩy về Langfuse Cloud với đầy đủ metadata tại `submission/evidence/trace-waterfall.txt`
- Langfuse Trace ID mẫu: `4b72c958f7cd78e7feb77f480e28818b` (xem tại `submission/evidence/trace-list.txt`)
- Giải thích một span đáng chú ý: Span `llm_generation` chứa chi tiết model (`claude-sonnet-4-5`), `prompt_tokens`: 36, `completion_tokens`: 168, `cost_usd`: $0.002628, `quality_score`: 0.9 và link Prompt version tương ứng.

## 4. Prompt versioning

- Prompt name: `day13-chat`
- Version/label baseline: `v1` (label: `baseline`, `production`)
- Version/label candidate: `v2` (label: `candidate`)
- Langfuse Trace ID của mỗi version: `4b72c958f7cd78e7feb77f480e28818b` (v1/production), `375483bad4fb6f5df15edc50244e7b43` (v2/candidate)
- Correlation ID của mỗi version: `req-35a4fc0c` (v1), `req-5ddb3119` (v2)
- Bằng chứng đổi label hoặc rollback: Đã tạo thành công v1 & v2 trên Langfuse API và thực thi switch/rollback thành công (chi tiết tại `submission/evidence/prompt-rollback.txt`).

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`: `HỢP LỆ: 6/6 panel có trong dashboard contract.`
- Evidence dashboard: `submission/evidence/dashboard-baseline.png`, `submission/evidence/dashboard-rag-slow.png` và `submission/evidence/dashboard-validator.txt`
- SLO đã chọn và lý do:
  - `latency_p95_ms`: Objective <= 3000ms (Target 99.5%) - Đảm bảo trải nghiệm tương tác trực tiếp không bị trễ.
  - `error_rate_pct`: Objective <= 2% (Target 99.0%) - Duy trì độ tin cậy và sẵn sàng của API.
  - `window_cost_usd`: Objective <= $2.50 trong cửa sổ dashboard 60 phút - Quản lý ngân sách token LLM khớp với panel Cost trên Dashboard.
  - `quality_score_avg`: Objective >= 0.75 (Target 95.0%) - Đảm bảo chất lượng câu trả lời từ RAG & FakeLLM.
- Alert rules và runbook: 3 quy tắc cảnh báo symptom-based được khai báo tại `config/alert_rules.yaml` (`HighLatencyP95`, `HighErrorRate`, `DegradedResponseQuality`) kết nối trực tiếp với tài liệu hướng dẫn khắc phục sự cố tại `docs/alerts.md`.

## 6. Điều tra challenge

- Challenge ID: `day13-k4-observability-v1`
- Triệu chứng từ metrics: P95 Latency tăng đột biến từ baseline ~154ms lên **2655ms** trên Dashboard/Panel Latency, làm kích hoạt cảnh báo vi phạm SLO Latency (threshold ≤ 2000ms).
- Langfuse Trace ID liên quan: `f59014d99605ccc1fd36d9e2db099251` (session `k4-challenge-s01`), `b98eee300257559f2dba70bd559b294a` (session `k4-challenge-s02`)
- Log line/correlation ID liên quan: `correlation_id: req-5adf5947`, `trace_id: f59014d99605ccc1fd36d9e2db099251`, event `response_sent`, `latency_ms: 2655`, `feature: "monitoring"`, `user_id_hash: f00ba60b3772` trong `data/logs.jsonl`
- Root cause: Incident `rag_slow` kích hoạt delay nhân tạo 2.5 giây (`time.sleep(2.5)`) trong hàm `retrieve()` của RAG sub-component (`app/mock_rag.py`) cho tất cả các query có feature `monitoring`.
- Fix action: Vô hiệu hóa sự cố bằng API `/incidents/rag_slow/disable` (thông qua `scripts/inject_incident.py --disable`), đưa latency tổng về mức bình thường ~158ms.
- Preventive measure: Thiết lập Timeout cho lệnh gọi RAG retrieval (max timeout 1.5s) kèm Fallback Cache/Local Index, cấu hình Alert Rule `HighLatencyP95` để tự động ngắt mạch (Circuit Breaker) khi P95 vượt ngưỡng 2000ms.

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| Trịnh Hoàng Nam (2A202601376) | Role A: API Middleware, gán Correlation ID xuyên suốt header và structlog context | [Commit Branch Role 1](https://github.com/dhquan04/K4-DAY13-2A202602034/commits/role1) | Hiểu cách truyền correlation ID giữa middleware và contextvars |
| Đỗ Việt Tùng (2A202601876) | Role B: PII Redaction processor, lọc email, SĐT VN, CCCD, Credit Card | [Commit Branch Tung](https://github.com/dhquan04/K4-DAY13-2A202602034/commits/tung) | Nắm vững kỹ thuật scrub dữ liệu PII trước khi ghi log JSON |
| Đinh Hoàng Quân (2A202602034) | Role C: Metrics snapshot, đo đếm error rate & xây dựng Dashboard HTML 6 panel | [Commit Main Repo](https://github.com/dhquan04/K4-DAY13-2A202602034/commits/main) | Cách thiết kế Dashboard contract và trực quan hóa telemetry |
| Hoàng Thanh Sơn (2A202601848) | Role D: Thiết lập SLO, viết Alert rules YAML & xây dựng Alert Runbook | [Commit Branch Role 4](https://github.com/dhquan04/K4-DAY13-2A202602034/commits/role4) | Kỹ năng định nghĩa SLO/Thresholds và xử lý alert theo runbook |
| Vũ Bảo Chinh (2A202601448) | Role E: Bọc sub-component trace RAG/LLM, chạy load test, điều tra CP3 Challenge & hoàn thiện Report | [Commit Branch Role E](https://github.com/dhquan04/K4-DAY13-2A202602034/commits/roleE) | Quy trình truy vết 3 lớp Metrics -> Traces -> Logs để tìm Root Cause |
