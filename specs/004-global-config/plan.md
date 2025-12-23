# Implementation Plan: Global Config CLI

**Branch**: `004-global-config-cli` | **Date**: 2025-12-23 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-global-config/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Add CLI commands (`gmuse config view` and `gmuse config set`) to allow users to view and modify their global configuration (`~/.config/gmuse/config.toml`) without manually editing files. The implementation extends the existing `typer` CLI, adds TOML writing capability via `tomlkit`, validates keys against the existing `DEFAULTS` allowlist in `config.py`, and provides clear output showing file contents, merged values, and override warnings.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: typer>=0.9.0, tomli>=2.0.0 (Python 3.10 only), tomlkit (new, for TOML writing)
**Storage**: XDG config file at `~/.config/gmuse/config.toml` (TOML format)
**Testing**: pytest, pytest-cov
**Target Platform**: Cross-platform (Linux, macOS, Windows)
**Project Type**: Single CLI package
**Performance Goals**: View/set operations complete in <100ms (local file I/O only)
**Constraints**: No network calls for config commands; preserve existing file comments/formatting
**Scale/Scope**: Single-user CLI tool, ~10-15 config keys

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

All feature plans MUST validate against the `gmuse` Constitution. At minimum, the following checks MUST be documented and verified:

### Pre-Design Gate Check

| Gate | Status | Notes |
|------|--------|-------|
| **Code Quality Gate** | ✅ PASS | New CLI subcommand group (`config`) with `view` and `set` commands. Extends existing `typer` patterns. New module `cli/config.py`. Type hints and docstrings required. Adds `tomlkit` dependency for TOML writing. |
| **Testing Gate** | ✅ PASS | Unit tests for config read/write/validate. Integration tests for end-to-end CLI. Coverage target: 90%+ for new module. Tests in `tests/unit/test_cli_config.py` and `tests/integration/test_cli_config.py`. |
| **UX Gate** | ✅ PASS | CLI help text with examples. Clear error messages for invalid keys/values. Docs update in `docs/source/how_to/configuration.md`. Override warnings in view output. |
| **Performance Gate** | ✅ PASS | Local file I/O only (<100ms). No network calls. No memory concerns for small config files. |

### Constitution Conformance Checklist

- [x] Public functions typed and documented with Google-style docstrings
- [x] Tests exist for every public function/command
- [x] Error messages are actionable with remediation steps
- [x] CLI follows typer/git-like conventions
- [x] No API keys stored in config (credentials remain env-based)
- [x] Semantic versioning followed (minor bump for new feature)
- [x] Documentation updated for new commands

## Project Structure

### Documentation (this feature)

```text
specs/004-global-config/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── cli-config.md    # CLI command contracts
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/gmuse/
├── config.py            # Existing - add ALLOWED_CONFIG_KEYS, write functions
├── cli/
│   ├── main.py          # Existing - register config subcommand group
│   └── config.py        # NEW - config view/set command implementations

tests/
├── unit/
│   ├── test_cli_config.py       # NEW - unit tests for config commands
│   └── test_config_write.py     # NEW - unit tests for config writing
└── integration/
    └── test_cli_config.py       # NEW - integration tests for config CLI
```

**Structure Decision**: Single project structure (existing). New CLI module `cli/config.py` mirrors existing pattern from `cli/completions.py`. Config writing functions added to existing `config.py` module.

## Complexity Tracking

No constitution violations. The feature is a straightforward extension of existing patterns:

- Uses existing `typer` CLI infrastructure
- Uses existing `config.py` validation functions
- Adds minimal new dependency (`tomlkit`) with clear justification (TOML writing not supported by `tomllib`)
