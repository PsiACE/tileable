# Examples

The `examples/` directory contains runnable scripts that double as integration tests and living documentation. Start with the greeting workflow and then customise it for your own tiles.

## Greeting walkthrough

```bash
python -m examples.greeting
```

This prints the observable lifecycle:

```text
[debug] {'tile': 'greeting', 'message': 'Tileable'}
Hi, Tileable!
runs=1
```

Behind the scenes:

1. `GreetingPlugin` contributes `GreetingTile` via `tile_specs` and seeds the context with a `prefix` service.
2. `invoke_tile` attaches a `TileContext`, emits lifecycle events, and executes the tile.
3. `EventBus.record()` captures `tile.debug` payloads while the plugin increments a shared `runs` counter.

## Drive the workflow from code

```python
from examples.greeting import GreetingPayload, run_greeting, showcase

# Direct execution with an explicit prefix
result = run_greeting(prefix="Yo", name="Builder")
print(result.response)

# Plugin-powered execution with event capture and shared state
result, debug_events, state = showcase(message="Tileable")
print(debug_events)
print(state["runs"])
```

## Capture more insight

Need the context that was active during a run? Ask for it explicitly:

```python
from tileable import invoke_tile

result, ctx = invoke_tile(
    "greeting",
    GreetingPayload(message="Inspector"),
    return_context=True,
)

print(dict(ctx.services))
print(ctx.state)
```

Wrap this pattern in your own tests to assert on services, state, or emitted events:

```python
from tileable import EventBus, invoke_tile

bus = EventBus()
with bus.record() as lifecycle:
    invoke_tile(..., event_bus=bus)

assert lifecycle.payloads("tile.failed") == []
```

Explore `tests/test_examples.py` for how we keep these demos verified end to end.
