# gmuse Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-11-28

## Active Technologies
- Python 3.10+ (gmuse), Zsh 5.9 (shell script) + `gmuse` (internal), `zsh` (runtime) (002-zsh-completions)
- Filesystem (for cache, XDG_CACHE_HOME) (002-zsh-completions)
- Python 3.10+ + Typer (CLI), pytest (tests), Ruff (lint/format), pyrefly (type-check), LiteLLM (provider calls; must be avoided in dry-run) (003-msg-dry-run)
- Filesystem + git repository state (staged diff, optional `.gmuse` file); N/A for new persistent storage (003-msg-dry-run)
- Python 3.10+ + typer>=0.9.0, tomli>=2.0.0 (Python 3.10 only), tomlkit (new, for TOML writing) (004-global-config-cli)
- XDG config file at `~/.config/gmuse/config.toml` (TOML format) (004-global-config-cli)
- Python 3.10+ (project minimum) + Sphinx, myst-parser, autodoc2, sphinx-copybutton, sphinx-design (existing docs stack) (001-prompt-template-docs)
- N/A (documentation generation only) (001-prompt-template-docs)

- Python 3.10+ (existing project requirement) (001-llm-commit-messages)

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
- 004-global-config-cli: Added Python 3.10+ + typer>=0.9.0, tomli>=2.0.0 (Python 3.10 only), tomlkit (new, for TOML writing)
- 005-prompt-template-docs: Added Python 3.10+ (project minimum) + Sphinx, myst-parser, autodoc2, sphinx-copybutton, sphinx-design (existing docs stack)
- 003-msg-dry-run: Added Python 3.10+ + Typer (CLI), pytest (tests), Ruff (lint/format), pyrefly (type-check), LiteLLM (provider calls; must be avoided in dry-run)
- 002-zsh-completions: Added Python 3.10+ (gmuse), Zsh 5.9 (shell script) + `gmuse` (internal), `zsh` (runtime)


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
