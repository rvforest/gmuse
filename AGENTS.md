# AGENTS.md

This file provides essential project information and development standards for coding agents working on the gmuse project.

## Project Overview

**gmuse** is a Python application for creating AI generated commit messages based on code changes.
- **Repository**: https://github.com/rvforest/gmuse
- **Documentation**: https://gmuse.readthedocs.io
- **License**: MIT
- **Python Version**: 3.10+
- **Main Dependencies**: No runtime dependencies by default. Development and documentation dependencies are defined in `pyproject.toml` (dev: Ruff, pyrefly, pytest, pytest-cov, pre-commit, nox; docs: Sphinx, myst-parser, furo, sphinx-autodoc2)

### Key Features

- **AI-powered commit messages**: Generate commit messages from staged git changes using LLM providers (OpenAI, Anthropic, Google, etc.)
- **Multiple formats**: Support for freeform, conventional commits, and gitmoji formats
- **Branch context** (optional): Include sanitized branch name information to improve message generation accuracy
- **Privacy-first**: Branch context is opt-in with automatic sanitization (masks ticket IDs, removes usernames, etc.)
- **Configurable**: CLI flags, environment variables, and configuration file support

## Architecture Overview

The project is organized into several core components:

### Directory Structure

The project follows a standard layout:

- `src/gmuse/` — package source
- `tests/` — test suite mirroring the `src/` structure
- `docs/` — documentation source and build files
- `noxfile.py` — nox sessions for running tests, docs, linting, and other tasks
- `.github/` — CI workflows
- `.pre-commit-config.yaml` — local pre-commit hooks configuration


## Development Standards

### Development Environment Setup

1. **Prerequisites**: Python 3.10+, Git, uv package manager
2. **Setup**: Run `uv sync` to create virtual environment and install dependencies
3. **Workflow**: Create feature branches, make changes, test, commit, and open PRs

### Code Quality Standards

#### Code Style and Formatting
- **Tool**: Ruff (Black-compatible formatting + linting)
- **Commands**:
  - Format code: `uv run nox -s format`
  - Check linting: `uv run nox -s lint`
  - Check all: `uv run nox -s check`

#### Type Hints
- **Required**: All public functions, classes, and methods must have type hints
- **Tool**: pyrefly for static type checking
- **Command**: `uv run nox -s types`

#### Documentation
- **Style**: Google-style docstrings for all public APIs
- **Tool**: Sphinx with autodoc2, myst_parser extensions
- **Commands**:
  - Build docs: `uv run nox -s docs`
  - Live docs: `uv run nox -s livedocs`
- Include usage examples in docstrings where applicable.

#### Naming Conventions

- **Project name**: kebab-case (lowercase, words separated by `-`), e.g. `my-awesome-package` (`project_name`)
- **Python package**: snake_case (lowercase, underscores), e.g. `my_awesome_package` (`package_name`)
- **Module and file names**: snake_case
- **Class names**: PascalCase
- **Constants**: UPPER_SNAKE_CASE
- **CLI commands**: kebab-case


### Testing Standards

This project uses pytest for testing, with a focus on unit tests and integration tests.

#### Framework and Coverage
- **Framework**: pytest
- **Coverage**: pytest-cov
- **Commands**:
  - Run tests: `uv run nox -s test`
  - Coverage report: `uv run nox -s coverage`

#### Test Organization
- Tests are organized in `tests/` directory, mirroring `src/` structure

### Pre-commit Hooks and CI

#### Pre-commit Hooks
- **Enabled**: Ruff linting/formatting, pyrefly type checking, yaml validation
- **Spell checking**: cspell for Markdown files only
- **Security**: detect-secrets for credential scanning
- **Setup**: Automatically configured with `uv sync`

#### Continuous Integration
- **Platform**: GitHub Actions
- **Checks**: All pre-commit hooks, tests across Python 3.10–3.13, coverage reporting

## Making Changes

### Workflow for Agents

1. **Understanding**: Review existing code, tests, and documentation before making changes
2. **Minimal Changes**: Make the smallest possible changes to achieve the goal
3. **Testing**: Run relevant tests early and frequently
4. **Quality**: Ensure code passes all linting, formatting, and type checking
5. **Documentation**: Update docstrings and docs if changing public APIs



### Common Commands

```bash
# Setup development environment
uv sync

# Run all quality checks
uv run nox -s check

# Run tests
uv run nox -s test

# Build documentation
uv run nox -s docs

# Format and lint code
uv run nox -s format
uv run nox -s lint
```

### Configuration Options

The project supports configuration through CLI flags, environment variables, and a config file (`~/.config/gmuse/config.toml`).

#### Core Configuration

- **model**: LLM model to use (e.g., `gpt-4`, `claude-3-opus`)
- **format**: Message format (`freeform`, `conventional`, `gitmoji`)
- **history_depth**: Number of recent commits for style context (0-50, default: 5)
- **timeout**: API timeout in seconds (5-300, default: 30)
- **copy_to_clipboard**: Auto-copy generated message to clipboard (default: false)

#### Branch Context Configuration (Privacy-Aware)

- **include_branch**: Include current branch name as context (default: `false`)
  - CLI: `--include-branch`
  - Environment: `GMUSE_INCLUDE_BRANCH=true`
  - Config file: `include_branch = true`

- **branch_max_length**: Maximum length for branch summary (20-200, default: 60)
  - Environment: `GMUSE_BRANCH_MAX_LENGTH=80`
  - Config file: `branch_max_length = 80`

**Privacy & Sanitization**: When `include_branch` is enabled:
- Branch names are normalized and lowercased
- Ticket IDs (e.g., JIRA-123, PROJ-456) are masked as `ticket-xxx`
- Usernames and long hex hashes are removed
- Default branches (main, master, develop) are automatically excluded
- Long branch names are truncated to `branch_max_length`

**Example:**
```bash
# With branch context
gmuse msg --include-branch

# Branch "feature/PROJ-123-add-authentication" becomes:
# - Branch type: "feature"
# - Branch summary: "ticket-xxx/add/authentication"
```

### Important Notes

- **Spell checking**: Only Markdown files are spell-checked; add technical terms to `cspell.json`
- **API stability**: Public APIs are stable within major versions (after v1.0)
- **Backwards compatibility**: Maintain compatibility when making changes to public APIs


## Resources

- **Contributing Guide**: `docs/source/development/contributing.md`
- **Development Guide**: `docs/source/development/development_guide.md`
- **Documentation**: https://gmuse.readthedocs.io

## Contact

For questions or issues, open an issue on GitHub or refer to the contributing guidelines.
