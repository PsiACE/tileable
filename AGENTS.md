# Repository Guidelines

## Project Structure & Module Organization
`src/tileable/` houses the runtime core (`runtime.py`), plugin wiring (`plugins.py`, `registry.py`), schemas, and public exports via `__init__.py`. Keep new modules inside this package and expose them only once stable. Tests mirror the package in `tests/` (e.g. `test_tiles.py`). Documentation lives in `docs/`, runnable demos now live under `examples/`, and build/tooling definitions stay in `pyproject.toml`, `tox.ini`, and the root `Makefile`.

## Build, Test, and Development Commands
- `make install` — create the uv-managed virtualenv and install pre-commit hooks.
- `make check` — run linting, type checking, and dependency hygiene (`ruff`, `ty`, `deptry`).
- `make test` — execute pytest plus doctests under Python 3.12 via uv.
- `tox -e py312,py313` — validate across supported interpreters and emit coverage XML.
- `uv run mkdocs serve` — live-preview the documentation site locally.

## Coding Style & Naming Conventions
Target Python 3.12+ and embrace KISS: prefer small, composable functions and lean on the standard library before new dependencies. Four-space indentation, type hints on public APIs, and concise docstrings are expected. Ruff enforces formatting (120-char lines) and lint rules; use `uv run pre-commit run -a` or `uv run ruff format` instead of manual fixes. Use snake_case for modules/functions, PascalCase for classes, and align plugin identifiers with their registry names.

## Testing Guidelines
Pytest with doctest support is authoritative. Place new tests beside related modules using `test_<module>.py` and `test_*` names. Favour deterministic assertions over brittle snapshots; for cross-module flows, stage integration tests inside `tests/runtime/`. Run `make test` for fast feedback and `tox -e py312,py313` before submitting to confirm compatibility and refresh `coverage.xml`. Exercise every new branch of control flow.

## Commit & Pull Request Guidelines
Write clean, imperative commit subjects (`Add plugin lookup guard`) and keep each commit focused. Before opening a PR, ensure `make check` and `make test` succeed, update docs when behavior shifts, and include payload samples or screenshots for user-facing changes. Reference related issues, request reviewers familiar with the affected area, and describe the verification commands in the PR body. PRs that land with lint/test green status move fastest.

## Dependency & Design Preferences
Default to project internals and the Python 3.12 standard library before adding third-party packages. If a new dependency is unavoidable, document the rationale in the PR and add it to the appropriate dependency group. Always validate that pre-commit hooks pass locally to keep the main branch lint-clean.
