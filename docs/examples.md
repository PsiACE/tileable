# Examples

Tileable ships with runnable scripts under the `examples/` directory. They double as integration tests and living documentation.

## Greeting walkthrough

```bash
python examples/greeting.py
```

Output:

```text
[debug] {'tile': 'greeting', 'message': 'Tileable'}
Hi, Tileable!
runs=1
```

What happened?

1. `GreetingPlugin` contributes `GreetingTile` through `tile_specs` and seeds the `TileContext` with a `prefix` service.
2. The runtime resolves the tile, emits lifecycle events, and the event bus captures `tile.debug` payloads.
3. The plugin counts each invocation by mutating the shared state, surfaced at the end of the run.

## Running custom payloads

You can also import the helpers directly:

```python
from examples.greeting import run_greeting, showcase

custom = run_greeting(prefix="Yo", name="Builder")
print(custom.response)

result, debug_events, state = showcase(message="Tileable")
```

Explore the tests in `tests/test_examples.py` to see how the examples stay verified.
