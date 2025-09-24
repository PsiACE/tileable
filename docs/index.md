# tileable

Welcome to Tileable, a modular workflow runtime for Python 3.12+ that keeps the developer journey focused on small, observable building blocks.

## Experience Goals

- **Start small, scale linearly.** Add one tile at a time without refactoring the world.
- **Stay observable.** Every execution emits lifecycle events you can log, stream, or test against.
- **Extend safely.** Plug-ins contribute tiles or lifecycle hooks without bypassing type checks or context guarantees.
- **Remain async-ready.** Synchronous and asynchronous paths share the same ergonomics.

## Tile Lifecycle at a Glance

1. A `Tile` subclass defines typed payload/result models (`TilePayload`, `TileResult`).
2. The runtime builds a `TileContext` that exposes services, shared state, and the event bus.
3. A `TileRegistry` resolves tile references (strings, classes, or instances).
4. `TilePluginManager` surfaces extra tiles and lifecycle hooks via pluggy.
5. `invoke_tile` / `ainvoke_tile` orchestrate execution, events, and cleanup.

## Build Your First Tile

Tileable ships with `examples/greeting.py`, a runnable end-to-end demo. Run it to see the full lifecycle:

```bash
python examples/greeting.py
```

Example output:

```text
[debug] {'tile': 'greeting', 'message': 'Tileable'}
Hi, Tileable!
runs=1
```

The README, documentation, and automated tests all reference the exact same code to keep examples aligned with runtime behavior:

```python
from examples.greeting import GreetingPayload, GreetingPlugin, GreetingTile, showcase
from tileable import EventBus, TilePluginManager, TileRegistry, invoke_tile

# Quick path: reuse the showcase helper
result, debug_events, state = showcase(message="Tileable")
print(debug_events)
print(result.response)
print(state["runs"])

# Manual assembly: registry + plugins + event bus
registry = TileRegistry()
plugins = TilePluginManager()
plugins.register(GreetingPlugin())

bus = EventBus()
bus.subscribe("tile.debug", lambda sender, **payload: print("debug", payload))

invoke_tile(
    "greeting",
    GreetingPayload(message="Operator"),
    registry=registry,
    plugins=plugins,
    event_bus=bus,
    state={"runs": 0},
)
```

Flow refresher:
1. The plugin surfaces `GreetingTile` via `tile_specs` and seeds services/state in `tile_startup`.
2. The runtime attaches a `TileContext`, emitting `runtime.*` and `tile.*` events along the way.
3. The event bus captures debug payloads, the tile returns a typed result, and state records run counts.
4. Lifecycle hooks still run on failure, ensuring cleanup.

## Async, Tested, and Documented
- Switch to `ainvoke_tile` for the same lifecycle with native async execution.
- Unit tests in `tests/` cover every component and example to guarantee stability.
- Documentation uses the MkDocs Terminal theme and publishes to <https://tileable.dev>.

## Next Steps
- Explore additional scripts under `examples/`.
- Dive into the API reference via the *Modules* navigation entry.
- Planning to contribute? Read `AGENTS.md` and `CONTRIBUTING.md`.
