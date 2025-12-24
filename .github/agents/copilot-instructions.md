# gmuse Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-11-28

## Active Technologies
- Python 3.10+ (project minimum)
- docs
  - Sphinx
  - myst-parser
  - autodoc2
  - sphinx-copybutton
  - sphinx-design
- implementaiton
  - Typer (CLI)
  - LiteLLM (provider calls)
  - TOML loader (tomllib/tomli)
- dev
  - pytest (tests)
  - Ruff (lint/format)
  - pyrefly


## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Code style MUST follow the `gmuse` Constitution: type hints, docstrings, Ruff-compatible formatting, and mypy type checks. Include links to the specific `pyproject.toml` sections and nox targets to run checks locally.

## Recent Changes
- 004-commit-message-max-chars: Added Python 3.10+ + Typer (CLI), LiteLLM (provider calls), TOML loader (tomllib/tomli), pytest (tests), Ruff (lint/format), pyrefly (type-check)
- 004-global-config-cli: Added Python 3.10+ + typer>=0.9.0, tomli>=2.0.0 (Python 3.10 only), tomlkit (new, for TOML writing)
- 005-prompt-template-docs: Added Python 3.10+ (project minimum) + Sphinx, myst-parser, autodoc2, sphinx-copybutton, sphinx-design (existing docs stack)
- 003-msg-dry-run: Added Python 3.10+ + Typer (CLI), pytest (tests), Ruff (lint/format), pyrefly (type-check), LiteLLM (provider calls; must be avoided in dry-run)
- 002-zsh-completions: Added Python 3.10+ (gmuse), Zsh 5.9 (shell script) + `gmuse` (internal), `zsh` (runtime)


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
