# tileable

Tileable is a modular workflow runtime for Python 3.12+ that keeps developers focused on observable, test-friendly building blocks.

## Getting started

```bash
python -m examples.greeting
```

You will see the full lifecycle play out:

```text
[debug] {'tile': 'greeting', 'message': 'Tileable'}
Hi, Tileable!
runs=1
```

The example is identical to how you would assemble components in production:

```python
from examples.greeting import GreetingPayload, GreetingPlugin, showcase
from tileable import EventBus, TilePluginManager, TileRegistry, invoke_tile

# Discover tiles via the bundled plugin
result, debug_events, state = showcase(message="Tileable")

# Or compose everything yourself
registry = TileRegistry()
plugins = TilePluginManager()
plugins.register(GreetingPlugin())
bus = EventBus()
state = {"runs": 0}

with bus.record() as lifecycle:
    invoke_tile(
        "greeting",
        GreetingPayload(message="Operator"),
        registry=registry,
        plugins=plugins,
        event_bus=bus,
        state=state,
    )

print(lifecycle.payloads("tile.debug"))
print(state["runs"])
```

## How a tile run works

1. A `Tile` subclass defines typed payload/result models (`TilePayload`, `TileResult`).
2. `invoke_tile` builds a `TileContext` exposing services, state, and `emit`.
3. `TileRegistry` resolves string/class/instance references.
4. `TilePluginManager` contributes tiles and lifecycle hooks via pluggy.
5. `EventBus` broadcasts `runtime.*` and `tile.*` events for instrumentation.

## Observe everything

`EventBus.record()` keeps event capture declarative:

```python
bus = EventBus()

with bus.record() as lifecycle:
    invoke_tile(..., event_bus=bus)

assert lifecycle.payloads("tile.failed") == []
```

Need raw subscribers? `bus.subscribe(name, handler)` returns an unsubscribe callback so you can tidy up easily.

## Reach into the context when you need it

Tiles and plugins collaborate via `TileContext`. Opt in to retrieving it by setting `return_context=True`:

```python
result, ctx = invoke_tile(
    "greeting",
    GreetingPayload(message="Developer"),
    return_context=True,
)

print(dict(ctx.services))
print(ctx.state.get("runs"))
```

During async runs, `ainvoke_tile(..., return_context=True)` behaves the same way.

## Scope runtime state for tests or multi-tenant hosts

```python
from tileable import scoped_runtime, TilePluginManager, TileRegistry

with scoped_runtime(registry=TileRegistry(), plugins=TilePluginManager()):
    ...  # run tiles without mutating global defaults
```

Pair this with dedicated `EventBus` instances to isolate observability per scenario.

## Async, tested, documented

- Switch to `ainvoke_tile` for native async execution—no API drift.
- Unit tests in `tests/` (plus doctests) keep behaviour locked in.
- MkDocs drives this site; run `uv run mkdocs serve` for live previews.

## Next steps

- Browse additional demos under `examples/`.
- Review the API reference via the *Modules* navigation entry.
- Planning to contribute? Read `AGENTS.md` and `CONTRIBUTING.md`.
