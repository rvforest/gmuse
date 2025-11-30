# Development Guide

This document is a development guide for maintainers of the gmuse project. It complements the Contributing Guide by covering in-depth procedures and developer-focused workflows.

## Overview

This guide includes:

- Development environment setup and how to manage the `uv` virtual environment
- Tests and CI details (nox sessions and GitHub Actions)
- Release and versioning process (versioningit/Hatch)
- How to add new dependencies and maintain `pyproject.toml`
- Documentation guidance
- Debugging tips and examples
- How to manage the changelog and releases
- Local debugging and running of CI tasks

## Getting started (maintainers)

### Environment

1. Install uv and local tools (see the UV docs): https://docs.astral.sh/uv/getting-started/installation/
2. Create and synchronize the virtual environment with dependencies:

```bash
uv sync
```

This will create or update the project's virtual environment, install dev dependencies, and configure `nox` to run tasks.

### Pre-commit

Install pre-commit hooks that help enforce project standards on local commits:

```bash
uv run pre-commit install
```

Use `uv run pre-commit run --all-files` to run all hooks locally across the repository.

## Development workflow

- Create a feature branch using the scoped naming convention (e.g., `feature/<short-desc>`, `fix/<short-desc>`)
- Add or update tests when adding or changing behavior
- Run unit and integration tests locally with nox:

```bash
uv run nox -s test
```

- Run linters and formatters:

```bash
uv run nox -s check
uv run nox -s format
uv run nox -s lint
```

- Run type checking:

```bash
uv run nox -s types
```

- Run doc builds before changing API docs:

```bash
uv run nox -s docs
```

## CI and GitHub Actions

- The GitHub Actions workflows automatically use `uv` and run the pre-commit hooks & nox sessions.
- Keep the workflows up to date in `.github/workflows/run-checks.yaml`.

## Testing details

- Unit tests are in `tests/` and mirror `src/gmuse/` structure
- Use `pytest` flags to increase verbosity and get better tracing:

```bash
uv run pytest -k "some_test_name" -vv
```

- Running coverage (see `noxfile.py`):

```bash
uv run nox -s coverage
```

## Documentation and Sphinx

- Documentation is built with Sphinx and uses `myst_parser` and `sphinx-autodoc2`.
- Update the `docs/source` index and add new pages in `docs/source/`.
- For local live preview:

```bash
uv run nox -s livedocs
```

## Adding or updating dependencies

- Add runtime dependencies to `project.dependencies` in `pyproject.toml` if a package is required for users.
- Add development or docs dependencies to the `dependency-groups` `dev` or `docs` sections respectively.
- To test installation flow:

```bash
uv build
pip install dist/*.whl
```

## Releasing a new version

- We use `versioningit` with Hatch to maintain versions. Release using your normal release process (tagging or Github workflows).
- When preparing a release: ensure tests pass and that `changelog` or release notes are updated.

## Debugging & common issues

- Locked package issues: run `uv sync --all-extras`.
- Test or linter failures: run `uv run nox -s <session-name>` locally to validate.
- If CI fails, check the failing job logs in the PR and run equivalent `nox` commands locally. Many failures can be reproduced using `UV_PROJECT_ENVIRONMENT` set to a replicated env.

## Fast checks for maintainers

- Quick static checks:

```bash
uv run nox -s check
```

- Quick formatting fix:

```bash
uv run nox -s format
```

- Run a single test module:

```bash
uv run pytest tests/test_some_module.py -q
```

## How to update docs for public APIs

- Update docstrings in source code and Sphinx markdown in `docs/source/`
- Include examples in the docstrings when applicable

## Housekeeping & repository rules for maintainers

- Keep dependency versions up-to-date; update `pyproject.toml` and make sure `uv` sync completes locally.
- Keep `cspell.json` entries accurate for new technical terms and acronyms in docs.
- Maintain minimal surface area for the public API; mark internal helpers as private.

## Contact

If you need help, open a GitHub issue or ping the maintainers (add them to the PR). For process changes (e.g., update CI), add a rationale in the PR description.

Thank you for maintaining gmuse!
