from app import metrics


def _reset_metrics() -> None:
    metrics.REQUEST_LATENCIES.clear()
    metrics.REQUEST_COSTS.clear()
    metrics.REQUEST_TOKENS_IN.clear()
    metrics.REQUEST_TOKENS_OUT.clear()
    metrics.QUALITY_SCORES.clear()
    metrics.ERRORS.clear()
    metrics.TRAFFIC = 0


def test_percentile_basic() -> None:
    assert metrics.percentile([100, 200, 300, 400], 50) >= 100


def test_error_rate_uses_received_requests_including_failed_requests() -> None:
    _reset_metrics()
    try:
        for _ in range(4):
            metrics.record_received()
        metrics.record_request(100, 0.01, 10, 20, 0.8)
        metrics.record_request(120, 0.01, 10, 20, 0.8)
        metrics.record_request(140, 0.01, 10, 20, 0.8)
        metrics.record_error("RuntimeError")

        snapshot = metrics.snapshot()

        assert snapshot["traffic"] == 4
        assert snapshot["error_rate_pct"] == 25.0
        assert snapshot["error_breakdown"] == {"RuntimeError": 1}
    finally:
        _reset_metrics()
