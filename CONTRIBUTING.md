# Contributing

## Adding a new module

Follow the pattern documented in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).
Concretely, a new module `Foo` needs:

1. `app/database/models/foo.py` — SQLAlchemy models, added to the import
   list in `app/database/models/__init__.py`.
2. `app/domain/foo_rules.py` — pure validation/state-machine functions,
   no SQLAlchemy imports.
3. `app/repositories/foo_repository.py` — subclasses of
   `app.repositories.base.BaseRepository[Model]`, adding only the
   domain-specific aggregate queries.
4. `app/services/foo_service.py` — orchestrates the repository + rules,
   wraps each public method with `@track("foo.<method>")` from
   `app.core.metrics`, logs via `get_logger("services.foo")`.
5. `app/pages/N_Foo.py` — a Streamlit page that only imports the service,
   never the repository or model directly.
6. Tests mirroring the above in `tests/test_domain/`,
   `tests/test_repositories/`, `tests/test_services/`, using the shared
   `session` fixture from `tests/conftest.py`.

Cross-module references must be plain foreign-key columns, not
`relationship()` objects that reach into another module's mapped class
— see [Architecture § Module boundaries](docs/ARCHITECTURE.md#module-boundaries).

## Before opening a PR

```bash
pytest
ruff check app tests scripts
```

Both must pass. If you added a new module, also update
[`docs/MODULES.md`](docs/MODULES.md).

## Code style

- Type hints everywhere; `from __future__ import annotations` at the top
  of every module.
- Minimal comments — only where the *why* isn't obvious from the code
  (a non-obvious invariant, a workaround). Don't restate what the code
  already says.
- No speculative abstractions: don't add configuration options, feature
  flags, or generalized helpers for a single call site.

## Publishing

This is a portfolio/reference project with no CI/CD pipeline configured.
To publish your own fork:

```bash
git remote add origin <your-repo-url>
git push -u origin main
```
