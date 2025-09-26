# Contrib Tiles — Opt-in power-ups

Tileable’s core stays lightweight. When you need extra muscle, reach for the
contrib tiles under `tileable.contrib`. Each capability remains “just a tile” so
Create, Combine, Repeat never stops being true.

> Optional extras: `pip install tileable[logfire]` for telemetry or
> `pip install tileable[huey]` for queue integration.

## Observability (`tileable.contrib.observability`)

```python
from tileable import EventBus, TilePluginManager, TileRegistry, invoke_tile
from tileable.contrib.observability import (
    LogfireObserverPayload,
    LogfireObserverPlugin,
    LogfireObserverTile,
)

registry = TileRegistry()
registry.register(MyBusinessTile)

plugins = TilePluginManager()
plugins.register(LogfireObserverPlugin())  # inject logfire or fallback logger

bus = EventBus()
result = invoke_tile(
    LogfireObserverTile,
    LogfireObserverPayload(tile="my-business", payload=MyPayload(...), registry=registry),
    registry=registry,
    plugins=plugins,
    event_bus=bus,
)
```

Interception is opt-in: wrap only the tile you care about, register the plugin
globally, or combine both. The observer emits `tile.observer.started`/
`completed` events and works with any emitter that exposes an `.emit(...)`
method.

## Retry (`tileable.contrib.retry`)

```python
from tileable import invoke_tile
from tileable.contrib.retry import RetryPayload, RetryPolicy, RetryTile

invoke_tile(
    RetryTile,
    RetryPayload(
        tile="inventory-sync",
        payload=SyncPayload(...),
        policy=RetryPolicy(max_attempts=5, backoff=0.1, jitter=0.05),
        registry=registry,
    ),
    registry=registry,
)
```

Retries emit `tile.retrying` events, respect allow/deny lists of exceptions, and
work for both sync and async tiles.

## Replay (`tileable.contrib.replay`)

```python
from tileable.contrib.replay import ReplayPayload, ReplayRecorder, ReplayTile

with ReplayRecorder(bus, "tile.debug") as recorder:
    invoke_tile("audit", AuditPayload(value=3), registry=registry, event_bus=bus)

seed = recorder.to_seed(tile="audit", payload=AuditPayload(value=3))
seed.save("audit-seed.json")

result = invoke_tile(
    ReplayTile,
    ReplayPayload(seed_path="audit-seed.json", registry=registry),
    registry=registry,
)
assert result.matches
```

Seeds capture payloads, optional services/state snapshots, and recorded events
so you can reproduce or fuzz later.

## Huey queue (`tileable.contrib.huey`)

```python
from tileable import TilePluginManager, invoke_tile
from tileable.contrib.huey import HueyDispatchPayload, HueyDispatchTile, HueyPlugin

plugins = TilePluginManager()
plugins.register(HueyPlugin(my_huey_dispatcher))

invoke_tile(
    HueyDispatchTile,
    HueyDispatchPayload(tile="add", payload=AddPayload(value=5), registry=registry),
    registry=registry,
    plugins=plugins,
)
```

The dispatch tile enqueues work using any dispatcher exposing
`enqueue(tile=..., payload=...)`. Pair it with `HueyWorkerTile` inside worker
processes to execute queued tasks. Tests in `tests/contrib/test_huey.py` cover
both fake and real Huey flows.

## Event flow (`tileable.contrib.flow`)

Build orchestration tiles by mapping emitted events to follow-up logic:

```python
from tileable.contrib.flow import EventFlowPayload, Subscription, register_event_flow

def fetch_router(bus, sender, data):
    ...  # decide which tile to invoke next based on payload/result

flow_tile = register_event_flow(
    Subscription("flow.fetch.completed", fetch_router),
    Subscription("flow.score.completed", score_router),
)

invoke_tile(
    flow_tile,
    EventFlowPayload(entry_tile="fetch", entry_payload=FetchPayload(...), registry=registry),
    registry=registry,
    event_bus=bus,
)
```

See `examples/orchestration.py` (and the matching test in `tests/test_examples.py`) for a complete branch/aggregate pipeline constructed this way.

Each contrib tile is verified by `tests/contrib/` so you can copy-and-paste with
confidence.
