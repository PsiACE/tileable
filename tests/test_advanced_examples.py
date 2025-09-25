from __future__ import annotations

from examples.context_inspection import inspect_context
from examples.multi_tile_workflow import run_multi_tile_workflow
from examples.scoped_isolation import run_in_isolation
from tileable.runtime import get_plugins, get_registry


def test_inspect_context_returns_services_state_and_events() -> None:
    result, services, state, events = inspect_context(user="agent")

    assert result.summary == "processed:agent"
    assert services["user"] == "agent"
    assert state["invocations"] == 1
    assert events == [{"tile": "audit", "user": "agent", "count": 1}]


def test_run_in_isolation_does_not_mutate_defaults() -> None:
    original_registry = get_registry()
    original_plugins = get_plugins()

    response = run_in_isolation(message="Tenant")

    assert response == "Hi, Tenant!"
    assert get_registry() is original_registry
    assert get_plugins() is original_plugins


def test_run_multi_tile_workflow_coalesces_state_and_events() -> None:
    summary, state, events = run_multi_tile_workflow(topic="demo")

    assert summary == "notified:demo"
    assert state["log"] == ["prepared:demo", "notified:demo"]
    assert events == [
        {"tile": "prepare", "entry": "prepared:demo"},
        {"tile": "notify", "entry": "notified:demo"},
    ]
