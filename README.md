# tileable

[![Release](https://img.shields.io/github/v/release/psiace/tileable)](https://img.shields.io/github/v/release/psiace/tileable)
[![Build status](https://img.shields.io/github/actions/workflow/status/psiace/tileable/main.yml?branch=main)](https://github.com/psiace/tileable/actions/workflows/main.yml?query=branch%3Amain)
[![Commit activity](https://img.shields.io/github/commit-activity/m/psiace/tileable)](https://img.shields.io/github/commit-activity/m/psiace/tileable)
[![License](https://img.shields.io/github/license/psiace/tileable)](https://img.shields.io/github/license/psiace/tileable)

Tileable is a Python 3.12+ framework for building modular, event-driven workflows out of tiny, well-typed “tiles”. It emphasises clarity (KISS), internal reuse, and complete testability.

- **Repository**: <https://github.com/psiace/tileable/>
- **Documentation**: <https://tileable.dev/>
- **Runnable demos**: `examples/` (`python -m examples.greeting`)

## Design Principles
- **Predictable primitives** — Tiles are simple classes with explicit payload/result models.
- **Runtime ergonomics** — The registry, event bus, and plugin manager do the wiring so you can compose tiles rapidly.
- **State you can trust** — Service injection and per-run state live on a strongly-typed context object.
- **Observability first** — Every run emits lifecycle events that you can subscribe to or persist.

## Quick Tour

All docs and tests reference the executable example in `examples/greeting.py`. The snippet below can be run as-is:

```python
from examples.greeting import GreetingPayload, GreetingPlugin, GreetingTile, showcase
from tileable import EventBus, TilePluginManager, TileRegistry, invoke_tile

# 1. Observe the plugin-driven workflow shipped with the library
result, debug_events, state = showcase(message="Tileable")
print(debug_events)  # [{'tile': 'greeting', 'message': 'Tileable'}]
print(result.response)  # "Hi, Tileable!"
print(state["runs"])   # 1

# 2. Assemble the same components manually
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
)
```

Runtime flow:
1. The plugin contributes `GreetingTile` via `tile_specs` and seeds services/state in `tile_startup`.
2. `invoke_tile` resolves the tile, attaches a `TileContext`, and emits `runtime.*` / `tile.*` events.
3. The event bus surfaces debug payloads while the tile returns a strongly typed result.
4. Lifecycle hooks keep context and state aligned, even when exceptions occur.

## Core Concepts
- **Tile** — Subclass `tileable.Tile` and implement `execute` (and optionally `aexecute`).
- **TileContext** — Automatically injected context exposing services, state, and `emit`.
- **TileRegistry** — Tracks available tiles and resolves string references.
- **EventBus** — Lightweight blinker-backed pub/sub for runtime monitoring.
- **TilePluginManager** — Pluggy integration for discovering tiles or reacting to lifecycle events.

## Develop with Confidence

> Tileable requires Python 3.12+. Verify with `python --version` before syncing.

```bash
make install   # create uv environment + pre-commit hooks
make check     # lint, type-check, dependency hygiene
make test      # pytest (sync, async, doctests)
tox -e py312,py313  # matrix verification
uv run mkdocs serve # docs preview at http://localhost:8000
```

CI expects lint + test green before merge. Pre-commit hooks (`uv run pre-commit run -a`) keep formatting consistent.

## Learn More
- Read the full guide: <https://tileable.dev/>
- Explore runnable samples in `examples/`
- Consult `AGENTS.md` for contributor expectations and workflows.

---

Repository initiated with [fpgmaas/cookiecutter-uv](https://github.com/fpgmaas/cookiecutter-uv), heavily customised for Tileable’s design philosophy.
