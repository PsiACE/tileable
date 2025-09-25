"""Demonstrate isolating Tileable defaults with ``scoped_runtime``."""

from __future__ import annotations

from examples.greeting import GreetingPayload, GreetingPlugin
from tileable import TilePluginManager, TileRegistry, invoke_tile, scoped_runtime


def run_in_isolation(message: str = "Isolated") -> str:
    """Execute ``GreetingTile`` without mutating global runtime defaults."""

    registry = TileRegistry()
    plugins = TilePluginManager()
    plugins.register(GreetingPlugin())

    with scoped_runtime(registry=registry, plugins=plugins):
        result = invoke_tile("greeting", GreetingPayload(message=message))
    return result.response


def main() -> None:
    print(run_in_isolation())


if __name__ == "__main__":
    main()
