# Implementation Plan: zsh completions for gmuse

**Branch**: `002-zsh-completions` | **Date**: 2025-12-16 | **Spec**: [specs/002-zsh-completions/spec.md](specs/002-zsh-completions/spec.md)
**Input**: Feature specification from `specs/002-zsh-completions/spec.md`

## Summary

Implement zsh completions for `gmuse` that provide AI-generated commit messages. This involves a CLI command to emit the completion script (`gmuse completions zsh`) and a runtime helper (`gmuse completions-run`) to generate suggestions. The solution must be XDG-compliant, support caching and rate-limiting (potentially in zsh or Python), and handle edge cases like "no staged changes" gracefully.

## Technical Context

**Language/Version**: Python 3.10+ (gmuse), Zsh 5.9 (shell script)
**Primary Dependencies**: `gmuse` (internal), `zsh` (runtime)
**Storage**: Filesystem (for cache, XDG_CACHE_HOME)
**Testing**: `pytest` (Python unit/integration), Manual/Shell harness (zsh)
**Target Platform**: WSL2 Ubuntu (zsh 5.9)
**Project Type**: Python CLI
**Performance Goals**: Generation < 4s, Cache hit < 200ms
**Constraints**: Simple eval-based installation, no secrets leakage, offline fallback
**Scale/Scope**: Single feature, CLI extension

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Code Quality Gate**: Yes. New CLI commands (`completions`, `completions-run`) will be typed and documented. Zsh script will be commented.
- **Testing Gate**: Yes. Unit tests for `gmuse.cli.completions`. Integration tests for `completions-run` output. Manual zsh verification.
- **UX Gate**: Yes. `gmuse completions --help` added. Warning messages for "no staged changes".
- **Performance Gate**: Yes. Caching and rate-limiting required. Timeout handling.

## Project Structure

### Documentation (this feature)

```text
specs/002-zsh-completions/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
└── gmuse/
    └── cli/
        ├── completions.py  # New module for completions commands
        └── ...
tests/
├── unit/
│   └── test_cli_completions.py
└── integration/
    └── test_completions_run.py
```
