# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert 1: HighLatencyP95

- Tên: HighLatencyP95
- Severity: critical
- SLI/SLO liên quan: `latency_p95_ms` (Objective: <= 3000ms, Target: 99.5%)
- Điều kiện và thời gian duy trì: Latency p95 > 3000ms duy trì liên tục trong 5 phút
- Ảnh hưởng tới người dùng: Người dùng trải nghiệm phản hồi rất chậm, timeout hoặc gián đoạn luồng chat với AI Agent.
- Ba bước kiểm tra đầu tiên:
  1. Kiểm tra panel `Latency percentiles` trên Dashboard để xác định thời điểm latency bắt đầu tăng vọt.
  2. Mở Langfuse Traces đối với các request chậm, xem waterfall span để xác định giai đoạn chậm (Vector DB retrieval hay LLM generation).
  3. Tìm kiếm trong `data/logs.jsonl` theo `correlation_id` của request có latency cao để kiểm tra log chi tiết.
- Mitigation tạm thời: Giảm số lượng tài liệu retrieved từ RAG hoặc chuyển hướng traffic sang model fallback có độ trễ thấp hơn.
- Owner: oncall-engineer

## Alert 2: HighErrorRate

- Tên: HighErrorRate
- Severity: critical
- SLI/SLO liên quan: `error_rate_pct` (Objective: <= 2%, Target: 99.0%)
- Điều kiện và thời gian duy trì: Tỷ lệ lỗi (error_rate_pct) > 2% duy trì liên tục trong 5 phút
- Ảnh hưởng tới người dùng: Người dùng nhận được phản hồi lỗi 500 / request_failed khi gọi API.
- Ba bước kiểm tra đầu tiên:
  1. Kiểm tra panel `Error rate and breakdown` trên Dashboard để xem phân bón loại lỗi (`error_type`).
  2. Lọc log trong `data/logs.jsonl` có `event == "request_failed"` để đọc thông tin chi tiết trong `payload.detail`.
  3. Mở Trace trên Langfuse ứng với `correlation_id` bị lỗi để kiểm tra stack trace và nguyên nhân cụ thể.
- Mitigation tạm thời: Khởi động lại service nếu lỗi do memory leak, hoặc kích hoạt fallback response/retry logic nếu LLM API provider bị sự cố.
- Owner: oncall-engineer

## Alert 3: DegradedResponseQuality

- Tên: DegradedResponseQuality
- Severity: warning
- SLI/SLO liên quan: `quality_score_avg` (Objective: >= 0.75, Target: 95.0%)
- Điều kiện và thời gian duy trì: Quality score trung bình (quality_score_avg) < 0.75 duy trì liên tục trong 10 phút
- Ảnh hưởng tới người dùng: Câu trả lời từ AI Agent không đạt chất lượng, thiếu context phù hợp hoặc bị suy giảm do prompt mới.
- Ba bước kiểm tra đầu tiên:
  1. Kiểm tra panel `Quality proxy` trên Dashboard để xác định xu hướng sụt giảm chất lượng.
  2. Mở Langfuse Traces để kiểm tra metadata `prompt_version`, `prompt_label` xem có prompt version mới vừa được triển khai hay không.
  3. Đọc log `response_sent` có `quality_score` thấp trong `data/logs.jsonl` để kiểm tra `message_preview` và `answer_preview`.
- Mitigation tạm thời: Thực hiện rollback prompt label về phiên bản prompt trước đó đã được xác nhận ổn định.
- Owner: ai-platform-team

