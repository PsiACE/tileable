# tileable

[![Release](https://img.shields.io/github/v/release/psiace/tileable)](https://img.shields.io/github/v/release/psiace/tileable)
[![Build status](https://img.shields.io/github/actions/workflow/status/psiace/tileable/main.yml?branch=main)](https://github.com/psiace/tileable/actions/workflows/main.yml?query=branch%3Amain)
[![Commit activity](https://img.shields.io/github/commit-activity/m/psiace/tileable)](https://img.shields.io/github/commit-activity/m/psiace/tileable)
[![License](https://img.shields.io/github/license/psiace/tileable)](https://img.shields.io/github/license/psiace/tileable)

Tileable is a Python 3.12+ framework for composing event-driven workflows from small, typed “tiles”. It keeps ergonomics, observability, and testability front and centre.

## Quickstart

```bash
make install          # set up the uv environment + pre-commit hooks
python -m examples.greeting
```

Example output:

```text
[debug] {'tile': 'greeting', 'message': 'Tileable'}
Hi, Tileable!
runs=1
```

Prefer a REPL? The demo tile is wired exactly like production code:

```python
from examples.greeting import GreetingPayload, GreetingPlugin, showcase
from tileable import EventBus, TilePluginManager, TileRegistry, invoke_tile

# Discover tiles via the bundled plugin
result, debug_events, state = showcase(message="Tileable")

# Or assemble the pieces manually
registry = TileRegistry()
plugins = TilePluginManager()
plugins.register(GreetingPlugin())
bus = EventBus()
state = {"runs": 0}

with bus.record() as lifecycle:
    result = invoke_tile(
        "greeting",
        GreetingPayload(message="Operator"),
        registry=registry,
        plugins=plugins,
        event_bus=bus,
        state=state,
    )

print(result.response)
print(lifecycle.payloads("tile.debug"))
print(state["runs"])
```

## Why tiles feel good
- **Predictable primitives** — A tile is just a tiny class with typed payload/result models.
- **Observability first** — `EventBus.record()` captures lifecycle events without throwaway subscribers.
- **State you can trust** — Services and per-run state live on `TileContext`, keeping plugins and tiles aligned.
- **Plugins without pain** — `TilePluginManager` contributes tiles, startup hooks, and shutdown hooks on demand.

## Build, observe, extend

**Run tiles and capture context**

```python
from tileable import invoke_tile

result, ctx = invoke_tile(
    "greeting",
    GreetingPayload(message="Developer"),
    return_context=True,
)

print(result.response)
print(dict(ctx.services))      # services added during execution
print(ctx.state.get("runs"))
```

**Scope runtime state for tests**

```python
from tileable import scoped_runtime, TileRegistry

with scoped_runtime(registry=TileRegistry()):
    ...  # run tiles without touching the global defaults
```

**Listen in when you need full control**

```python
bus = EventBus()

unsubscribe = bus.subscribe("tile.failed", lambda sender, **payload: print(payload))
invoke_tile(..., event_bus=bus)
unsubscribe()
```

## Quality gates

```bash
make check    # ruff lint + formatter, ty type-checking, deptry hygiene
make test     # pytest (sync + async paths and doctests)
tox -e py312,py313  # interpreter matrix + coverage xml
```

CI expects these commands to pass before merging. Pre-commit hooks (`uv run pre-commit run -a`) keep formatting aligned.

## Learn more
- Full documentation: <https://tileable.dev/>
- Additional demos: `examples/`
- Contributor handbook: `AGENTS.md`

---

Repository initiated with [fpgmaas/cookiecutter-uv](https://github.com/fpgmaas/cookiecutter-uv), heavily customised for Tileable’s design philosophy.
