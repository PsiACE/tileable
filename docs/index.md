# tileable — Create. Combine. Repeat.

Welcome to Tileable: a modular workflow runtime that lets you assemble event-
driven systems from tiny, testable tiles. The developer experience rotates
around three verbs:

1. **Create** small, typed tiles.
2. **Combine** them with runtime services, context, and events.
3. **Repeat** the pattern with confidence thanks to observability and tests.

## 1. Create — define a tile

```python
from tileable import Tile, TilePayload, TileResult

class GreetingPayload(TilePayload):
    name: str

class GreetingResult(TileResult):
    message: str

class GreetingTile(Tile[GreetingPayload, GreetingResult]):
    name = "greeting"

    def execute(self, payload: GreetingPayload) -> GreetingResult:
        self.context.emit("tile.debug", tile=self.name, name=payload.name)
        return GreetingResult(message=f"Hi, {payload.name}!")
```

## 2. Combine — let the runtime do the wiring

```python
from tileable import EventBus, TilePluginManager, TileRegistry, invoke_tile

registry = TileRegistry()
registry.register(GreetingTile)

plugins = TilePluginManager()
bus = EventBus()

with bus.record() as lifecycle:
    result, ctx = invoke_tile(
        "greeting",
        GreetingPayload(name="Tileable"),
        registry=registry,
        plugins=plugins,
        event_bus=bus,
        return_context=True,
    )

print(result.message)
print(lifecycle.payloads("tile.debug"))
print(dict(ctx.services))
```

### Ergonomics out of the box

- `TileContext` injects services, shared state, and the event bus automatically.
- `EventBus.record()` captures lifecycle payloads without ad-hoc listeners.
- `scoped_runtime` swaps registries/plugins/bus for a single test or tenant.
- `invoke_tile(..., return_context=True)` hands back the post-run context when
  you need to inspect it.

## 3. Repeat — orchestrate and extend

### Event-driven orchestration

`examples/orchestration.py` uses `tileable.contrib.flow.register_event_flow`
to listen to tile events, branch on results, and aggregate histories across
fetch/score/notify tiles. The behaviour is verified by `tests/test_examples.py`
so documentation and runtime stay aligned.

### Contrib tiles

Install optional extras when you want richer behaviour:

```bash
pip install tileable[logfire]
pip install tileable[huey]
```

- `LogfireObserverTile` + `LogfireObserverPlugin` — telemetry (logs/traces/
  metrics) with zero boilerplate.
- `RetryTile` — exponential backoff with `tile.retrying` events.
- `ReplayTile` — record runs as JSON seeds and replay them later.
- `HueyDispatchTile` / `HueyWorkerTile` — push work to Huey queues while keeping
  business tiles untouched.

See `docs/contrib.md` and `docs/advanced.md` for complete recipes.

## Quality gates

```bash
make check    # linting, type checking, dependency hygiene
make test     # pytest across sync, async, contrib, orchestration
```

CI expects these commands to pass before merging. Pre-commit hooks (`uv run pre-commit run -a`) keep formatting aligned.

## Explore further

- `examples/` — runnable demos including `greeting` and `orchestration`
- `docs/examples.md` — walkthroughs and testing tips
- `docs/advanced.md` — context inspection, scoped runtime, multi-tile workflows
- `docs/contrib.md` — observer, retry, replay, Huey tiles
- `AGENTS.md` — contributor handbook

The modular framework for your ideas. Create. Combine. Repeat.
