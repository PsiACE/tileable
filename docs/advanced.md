# Advanced Usage

Ready to go beyond the basics? These recipes lean on Tileable’s core abstractions so you can tackle richer scenarios without leaving the KISS ethos.

## Inspect execution with `return_context`

`examples/context_inspection.py` shows how to collect services, shared state, and emitted events after a run:

```python
from examples.context_inspection import inspect_context

result, services, state, events = inspect_context(user="agent")

print(result.summary)           # "processed:agent"
print(services["user"])        # "agent"
print(state["invocations"])    # 1
print(events)                   # [{'tile': 'audit', 'user': 'agent', 'count': 1}]
```

Inside `inspect_context` we:

1. Register a custom `AuditTile` that mutates services/state during execution.
2. Capture debug events with `with EventBus().record("tile.debug")`.
3. Call `invoke_tile(..., return_context=True)` and surface a snapshot of the context.

You get the full execution footprint when you need it, while the default ergonomics stay minimal.

## Isolate runtime state with `scoped_runtime`

Need to swap out the global registry or plugin manager temporarily? `examples/scoped_isolation.py` keeps things contained:

```python
from examples.scoped_isolation import run_in_isolation

print(run_in_isolation("Tenant"))
# Hi, Tenant!
```

The pattern is straightforward:

1. Create dedicated `TileRegistry` / `TilePluginManager` instances and register the tiles you need.
2. Enter `with scoped_runtime(registry=..., plugins=...)` to override Tileable’s defaults.
3. When the scope exits, the previous instances are restored automatically.

## Coordinate multiple tiles

`examples/multi_tile_workflow.py` demonstrates how two tiles can collaborate via shared state and services:

```python
from examples.multi_tile_workflow import run_multi_tile_workflow

summary, state, events = run_multi_tile_workflow()

print(summary)          # "notified:demo"
print(state["log"])     # ["prepared:demo", "notified:demo"]
print(events)
```

Under the hood:

1. A preparation tile writes to shared state and emits a debug event.
2. A follow-up tile reads the state, adds another entry, and emits its own event.
3. Both invocations share the same `TileRegistry`, `EventBus`, and state dictionary, letting you orchestrate multi-step flows without extra infrastructure.

All of these advanced snippets are exercised in `tests/test_advanced_examples.py`, so you can copy them into your project with confidence. As your needs grow, assemble richer pipelines by composing more tiles—the core Tileable abstractions will keep things predictable and observable.
