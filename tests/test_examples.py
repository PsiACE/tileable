from __future__ import annotations

from examples.greeting import GreetingResult, run_greeting, showcase


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
