from __future__ import annotations

from examples.greeting import GreetingPayload, GreetingPlugin, GreetingResult, run_greeting, showcase
from tileable import EventBus, TilePluginManager, TileRegistry, invoke_tile


def test_run_greeting_uses_explicit_prefix() -> None:
    result = run_greeting(prefix="Yo", name="Agent")
    assert isinstance(result, GreetingResult)
    assert result.response == "Yo, Agent!"


def test_showcase_returns_debug_events_and_state() -> None:
    result, debug_events, state = showcase(message="Tileable")

    assert isinstance(result, GreetingResult)
    assert result.response == "Hi, Tileable!"

    assert debug_events == [{"tile": "greeting", "message": "Tileable"}]
    assert state["runs"] == 1


def test_readme_manual_wiring_matches_behavior() -> None:
    registry = TileRegistry()
    plugins = TilePluginManager()
    plugins.register(GreetingPlugin())
    bus = EventBus()
    state: dict[str, object] = {"runs": 0}

    with bus.record() as lifecycle:
        result = invoke_tile(
            "greeting",
            GreetingPayload(message="Operator"),
            registry=registry,
            plugins=plugins,
            event_bus=bus,
            state=state,
        )

    assert result.response == "Hi, Operator!"
    assert lifecycle.payloads("tile.debug") == [{"tile": "greeting", "message": "Operator"}]
    assert state["runs"] == 1
