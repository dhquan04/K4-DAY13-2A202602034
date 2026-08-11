from __future__ import annotations

STATE = {
    "rag_slow": False,
    "tool_fail": False,
    "cost_spike": False,
    "cost_optimization": False,
}


def enable(name: str) -> None:
    if name not in STATE:
        raise KeyError(f"Unknown incident: {name}")
    STATE[name] = True



def disable(name: str) -> None:
    if name not in STATE:
        raise KeyError(f"Unknown incident: {name}")
    STATE[name] = False


def set_cost_optimization(enabled: bool) -> None:
    """Toggle the response output-token cap used for the cost optimization bonus."""
    STATE["cost_optimization"] = enabled



def status() -> dict[str, bool]:
    return dict(STATE)
