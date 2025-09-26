# Examples

Tileable ships with runnable examples that mirror the documentation and test
suite. Each script can be launched directly, and every behaviour is validated by
pytest so you can trust what you read.

## Greeting walkthrough

```bash
python -m examples.greeting
```

Output:

```text
[debug] {'tile': 'greeting', 'message': 'Tileable'}
Hi, Tileable!
runs=1
```

What happened?

1. `GreetingPlugin` contributed `GreetingTile` via `tile_specs` and seeded the
   context with a `prefix` service and a `runs` counter.
2. The runtime attached a `TileContext`, emitted lifecycle events, and executed
   the tile.
3. The event bus captured `tile.debug` payloads while the tile returned a typed
   result.

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

The matching tests in `tests/test_examples.py` keep both entry points locked to
this behaviour.

## Capture more insight

Need the context or emitted events after a run? Opt in explicitly:

```python
from tileable import EventBus, invoke_tile

bus = EventBus()
with bus.record() as lifecycle:
    result, ctx = invoke_tile(
        "greeting",
        GreetingPayload(message="Inspector"),
        event_bus=bus,
        return_context=True,
    )

print(dict(ctx.services))
print(ctx.state)
print(lifecycle.payloads("tile.debug"))
```

## Event-driven orchestration

`examples/orchestration.py` builds an `EventFlowTile` via
`tileable.contrib.flow.register_event_flow`. The flow subscribes to
`flow.fetch.completed` and `flow.score.completed` events, decides whether to
branch into scoring or go straight to notification, and keeps per-order history
in shared state. Run it and inspect the aggregated summaries:

```bash
python -m examples.orchestration
```

The pipeline is validated by `tests/test_examples.py` (and the lower-level
`tests/contrib/test_flow.py`), so the branching logic remains deterministic.

## Where to next?

- `examples/context_inspection.py` — capture services/state/events for debugging.
- `examples/scoped_isolation.py` — isolate registry/plugins for tests.
- `examples/multi_tile_workflow.py` — coordinate tiles with shared state and
  services.

All example behaviours are enforced by matching tests. Modify with confidence,
then Create, Combine, Repeat for your own ideas.
