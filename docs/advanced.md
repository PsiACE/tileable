# Advanced Recipes

Tileable’s core primitives stay small, but you can layer additional behaviours
without losing the KISS experience. This page highlights a few patterns that
keep complex journeys manageable.

## Inspect execution with `return_context`

`examples/context_inspection.py` shows how to export the services, shared state,
and emitted events after a run:

```python
from examples.context_inspection import inspect_context

result, services, state, events = inspect_context(user="agent")

print(result.summary)           # "processed:agent"
print(services["user"])        # "agent"
print(state["invocations"])    # 1
print(events)                   # [{'tile': 'audit', 'user': 'agent', 'count': 1}]
```

The helper captures events via `EventBus.record()`, takes shallow copies of
services/state, and returns everything for debugging or assertions. The example
is exercised in `tests/test_advanced_examples.py` so behaviour stays aligned.

## Isolate runtime state with `scoped_runtime`

Need to override the default registry or plugin manager temporarily? Use the
scoped runtime helper, as in `examples/scoped_isolation.py`:

```python
from examples.scoped_isolation import run_in_isolation

response = run_in_isolation("Tenant")
print(response)  # Hi, Tenant!
```

Behind the scenes, the example registers tiles and plugins inside a `with
scoped_runtime(...)` block and restores the previous defaults afterwards. Tests
in `tests/test_advanced_examples.py` verify the isolation story.

## Coordinate multiple tiles

`examples/multi_tile_workflow.py` demonstrates how two tiles collaborate via
shared state and services:

```python
from examples.multi_tile_workflow import run_multi_tile_workflow

summary, state, events = run_multi_tile_workflow()

print(summary)      # "notified:demo"
print(state["log"]) # ["prepared:demo", "notified:demo"]
print(events)
```

The example—and its corresponding test in `tests/test_advanced_examples.py`—keep
multi-tile coordination predictable.

## Orchestrate with events

Want branching and aggregation without a heavyweight orchestrator? See
`examples/orchestration.py`, then copy the approach:

1. Subscribe to `tile.completed` on an `EventBus`.
2. Inspect the payload/result and decide which tile to call next.
3. Pass along shared state/services so downstream tiles operate on the same
   context.

The pipeline is covered in `tests/test_examples.py`, proving that event flows
are fully deterministic.

## Installing contrib extras

Many advanced recipes lean on contrib tiles. Install the extras when needed:

```bash
pip install tileable[logfire]
pip install tileable[huey]
```

Then consult `docs/contrib.md` for structured telemetry, retry policies, replay
seeds, or Huey-backed execution. Each capability is “just a tile”, so Create,
Combine, Repeat remains the guiding principle.
