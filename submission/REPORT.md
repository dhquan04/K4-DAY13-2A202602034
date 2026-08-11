
# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm: ChickenFarmer
- Repository URL: https://github.com/dhquan04/K4-DAY13-2A202602034
- Commit SHA cuối: d5934a78fefe5325a1f32cdcbc4c3c0fc319dc93
- Thành viên và vai trò:
  1. Đinh Hoàng Quân (2A202602034) - Role A: API & Middleware (Correlation ID, Exception Handlers)
  2. Hoàng Thanh Sơn (2A202601848) - Role B: Security Engineer (PII Redaction, Regex Patterns)
  3. Đỗ Việt Tùng (2A202601876) - Role C: Metrics & Dashboard (Error Rate, Dashboard Contract 6 Panel)
  4. Vũ Bảo Chinh (2A202601448) - Role D: SRE & Alerts Engineer (SLO, Alert Rules, Alert Runbook)
  5. Trịnh Hoàng Nam (2A202601376) - Role E: QA & Chief Investigator (Sub-component Tracing, Load test, Điều tra Challenge CP3 & Tổng hợp Báo cáo)

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: 100/100 (Pass 4/4 tiêu chí)
- Tổng số traces: 10+ traces (đã ghi nhận trên Langfuse Cloud)
- Số PII leak còn lại: 0
- Link/đường dẫn dashboard: /dashboard

## 3. Logging và tracing

- Evidence correlation ID: `req-580031ec` (truyền xuyên suốt HTTP header `x-request-id` và structlog contextvars)
- Evidence PII redaction: Đã kiểm chứng scrub toàn bộ email `[REDACTED_EMAIL]`, SĐT `[REDACTED_PHONE_VN]`, thẻ `[REDACTED_CREDIT_CARD]` trong `data/logs.jsonl`
- Evidence trace waterfall: Span `rag_retrieval` và `generation` ghi nhận đẩy về Langfuse Cloud với đầy đủ metadata
- Giải thích một span đáng chú ý: Span `generation` chứa chi tiết model (`claude-sonnet-4-5`), `prompt_tokens`, `completion_tokens`, `cost_usd`, `quality_score` và link Prompt version tương ứng.

## 4. Prompt versioning

- Prompt name: `day13-chat`
- Version/label baseline: `v1` (label: `baseline`, `production`)
- Version/label candidate: `v2` (label: `candidate`)
- Trace ID của mỗi version: `req-580031ec` (v1/production), `req-31d8d377` (v1/production)
- Bằng chứng đổi label hoặc rollback: Đã tạo thành công v1 & v2 trên Langfuse API và thực thi switch/rollback thành công.

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

- Challenge ID: `day13-k4-observability-v1`
- Triệu chứng từ metrics: P95 Latency tăng đột biến từ baseline ~150ms lên **2652ms** trên Dashboard/Panel Latency, làm kích hoạt cảnh báo vi phạm SLO Latency (threshold ≤ 2000ms).
- Trace ID liên quan: `req-49caccf1` (session `k4-challenge-s01`), `req-17696285` (session `k4-challenge-s02`)
- Log line/correlation ID liên quan: `correlation_id: req-49caccf1`, event `response_sent`, `latency_ms: 2652`, `feature: "monitoring"`, `user_id_hash: f00ba60b3772`
- Root cause: Incident `rag_slow` kích hoạt delay nhân tạo 2.5 giây (`time.sleep(2.5)`) trong hàm `retrieve()` của RAG sub-component (`app/mock_rag.py`) cho tất cả các query có feature `monitoring`.
- Fix action: Vô hiệu hóa sự cố bằng API `/incidents/rag_slow/disable` (thông qua `scripts/inject_incident.py --disable`), đưa latency tổng về mức bình thường ~150ms.
- Preventive measure: Thiết lập Timeout cho lệnh gọi RAG retrieval (ví dụ max timeout 1.5s) kèm Fallback Cache/Local Index, cấu hình Alert Rule `HighLatencyP95` để tự động ngắt mạch (Circuit Breaker) khi P95 vượt ngưỡng 2000ms.

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên                     | Phần việc                                                                                               | Commit/PR                                                    | Điều đã học                                                           |
| -------------------------------- | --------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ | -------------------------------------------------------------------------- |
| Đinh Hoàng Quân (2A202602034) | Role A: API Middleware, gán Correlation ID xuyên suốt header và structlog context                     | [Main Repo](https://github.com/dhquan04/K4-DAY13-2A202602034) | Hiểu cách truyền correlation ID giữa middleware và contextvars        |
| Hoàng Thanh Sơn (2A202601848)  | Role B: PII Redaction processor, lọc email, SĐT VN, CCCD, Credit Card                                   | [Main Repo](https://github.com/dhquan04/K4-DAY13-2A202602034) | Nắm vững kỹ thuật scrub dữ liệu PII trước khi ghi log JSON         |
| Đỗ Việt Tùng (2A202601876)   | Role C: Metrics snapshot, đo đếm error rate & xây dựng Dashboard HTML 6 panel                        | [Main Repo](https://github.com/dhquan04/K4-DAY13-2A202602034) | Cách thiết kế Dashboard contract và trực quan hóa telemetry          |
| Vũ Bảo Chinh (2A202601448)     | Role D: Thiết lập SLO, viết Alert rules YAML & xây dựng Alert Runbook                                | [Main Repo](https://github.com/dhquan04/K4-DAY13-2A202602034) | Kỹ năng định nghĩa SLO/Thresholds và xử lý alert theo runbook      |
| Trịnh Hoàng Nam (2A202601376)  | Role E: Bọc sub-component trace RAG/LLM, chạy load test, điều tra CP3 Challenge & hoàn thiện Report | [Main Repo](https://github.com/dhquan04/K4-DAY13-2A202602034) | Quy trình truy vết 3 lớp Metrics -> Traces -> Logs để tìm Root Cause |
