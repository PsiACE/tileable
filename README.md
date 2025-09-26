# tileable — Create. Combine. Repeat.

[![Release](https://img.shields.io/github/v/release/psiace/tileable)](https://img.shields.io/github/v/release/psiace/tileable)
[![Build status](https://img.shields.io/github/actions/workflow/status/psiace/tileable/main.yml?branch=main)](https://github.com/psiace/tileable/actions/workflows/main.yml?query=branch%3Amain)
[![Commit activity](https://img.shields.io/github/commit-activity/m/psiace/tileable)](https://img.shields.io/github/commit-activity/m/psiace/tileable)
[![License](https://img.shields.io/github/license/psiace/tileable)](https://img.shields.io/github/license/psiace/tileable)

Tileable is a Python 3.12+ runtime for developers who want to assemble modular,
event-driven workflows out of tiny, typed building blocks. Every tile is just a
class. Every run is observable. Every composition stays testable. **Create** a
tile, **combine** it with others, then **repeat** with confidence.

## Create — start small

```bash
make install          # set up the uv environment + pre-commit hooks
python -m examples.greeting
```

The quick start doubles as a living reference. It fetches a tile, wires it
through the runtime, and emits lifecycle events:

```text
[debug] {'tile': 'greeting', 'message': 'Tileable'}
Hi, Tileable!
runs=1
```

Prefer exploring in a REPL? The example is the same code you will ship:

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

with bus.record() as lifecycle:
    result = invoke_tile(
        "greeting",
        GreetingPayload(message="Operator"),
        registry=registry,
        plugins=plugins,
        event_bus=bus,
        state={"runs": 0},
    )

print(result.response)
print(lifecycle.payloads("tile.debug"))
```

## Combine — compose and observe

- **Predictable primitives** — Tiles are plain classes with typed payload/result
  models. `TileContext` injects services, shared state, and the event bus for you.
- **Observability first** — `EventBus.record()` captures lifecycle payloads.
  Prefer callbacks? `bus.subscribe(...)` returns an unsubscribe handle.
- **Isolation when you need it** — `scoped_runtime` swaps registries, plugins,
  or the event bus for one test or tenant, then restores previous defaults.
- **Context on demand** — `invoke_tile(..., return_context=True)` hands back the
  post-run context so you can inspect services or state snapshots.

```python
from tileable import scoped_runtime, invoke_tile, TileRegistry

with scoped_runtime(registry=TileRegistry()):
    result, ctx = invoke_tile(
        "greeting",
        GreetingPayload(message="Developer"),
        return_context=True,
    )
    print(result.response)
    print(dict(ctx.services))
```

## Repeat — scale your ideas

- **Event-driven orchestration** — `examples/orchestration.py` shows how to
  use `tileable.contrib.flow.register_event_flow` to listen for tile events,
  branch based on results, and aggregate run histories. The behaviour is locked
  in via `tests/test_examples.py`.
- **Contrib tiles** — Opt into the extras you need:
  - `LogfireObserverTile` (`pip install tileable[logfire]`) wraps runs with
    telemetry; pair with `LogfireObserverPlugin` for a zero-boilerplate setup.
  - `RetryTile` adds exponential backoff policies and emits `tile.retrying`
    events for observability.
  - `ReplayTile` records runs as JSON seeds and replays them later to reproduce
    or fuzz behaviour.
  - `HueyDispatchTile` / `HueyWorkerTile` (`pip install tileable[huey]`) push
    work to Huey queues while keeping business tiles untouched.

See `docs/contrib.md` and `docs/advanced.md` for deeper recipes.

## Quality gates

```bash
make check    # linting, type-checking, dependency hygiene
make test     # pytest (sync, async, contrib, orchestration)
tox -e py312,py313  # interpreter matrix + coverage
```

CI expects these commands to pass before merging. Pre-commit hooks (`uv run pre-commit run -a`) keep formatting aligned.

## Learn more
- Documentation & guides: <https://tileable.dev/>
- Examples: `examples/` (including `examples/orchestration.py`)
- Advanced recipes: `docs/advanced.md`
- Contrib reference: `docs/contrib.md`
- Contributor handbook: `AGENTS.md`

---

Repository initiated with [fpgmaas/cookiecutter-uv](https://github.com/fpgmaas/cookiecutter-uv), heavily customised for Tileable’s design philosophy.
