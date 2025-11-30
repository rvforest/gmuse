# Implementation Plan: LLM-Powered Commit Message Generator

**Branch**: `001-llm-commit-messages` | **Date**: 2025-11-28 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-llm-commit-messages/spec.md`

## Summary

The feature implements a CLI tool that generates commit messages using LLMs based on staged git changes. The tool will extract staged diffs, analyze recent commit history for style context, build prompts incorporating user instructions, and call LLM providers to generate contextual commit messages. The implementation prioritizes zero-config first-time use while supporting optional customization via configuration files and CLI flags.

## Technical Context

**Language/Version**: Python 3.10+ (existing project requirement)
**Primary Dependencies**:
- Typer (existing) - CLI framework
- LiteLLM - Unified LLM provider interface (supports OpenAI, Anthropic, etc.)
- pyperclip - Cross-platform clipboard operations
- GitPython - Git repository interactions (alternative: subprocess with git CLI)
- tomli/tomllib (stdlib 3.11+) - TOML config parsing

**Storage**:
- Configuration: `$XDG_CONFIG_HOME/gmuse/config.toml` (TOML file)
- Repository instructions: `.gmuse` file at repo root (plain text)

**Testing**: pytest (existing), pytest-cov (existing)
**Target Platform**: Cross-platform (Linux, macOS, Windows)
**Project Type**: Single CLI application (existing structure: src/gmuse/)

**Performance Goals**:
- Generation latency: <10s for typical diffs (<1000 lines)
- Token consumption: <8K tokens per prompt
- Network timeout: 30s default

**Constraints**:
- Zero runtime dependencies by default (LiteLLM/pyperclip optional)
- XDG Base Directory compliance for config/data storage
- Must work in git repositories only
- API keys via environment variables (no hardcoded secrets)

**Scale/Scope**:
- Single-user CLI tool
- Support for multiple concurrent repositories
- Support for diffs up to ~5000 lines (with intelligent truncation)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Code Quality Gate ✅

- **Public API Changes**: Yes - new CLI command `gmuse` with multiple flags (`--hint`, `--copy`, `--model`, `--format`, `--history-depth`)
- **Affected Modules**:
  - New: `src/gmuse/config.py` (config loading/validation)
  - New: `src/gmuse/git_utils.py` (git operations)
  - New: `src/gmuse/prompt_builder.py` (prompt assembly)
  - New: `src/gmuse/llm_client.py` (LLM provider interface)
  - Modified: `src/gmuse/cli/main.py` (add generate command)
- **Type Hints**: All public functions/classes will have complete type hints (mypy enforcement enabled)
- **Docstrings**: All public APIs will use Google-style docstrings with usage examples
- **Linting**: Ruff (existing) - all new code must pass
- **Mitigation**: Follow existing project patterns from `cli/main.py`, maintain modular design

### Testing Gate ✅

- **Unit Tests Required**:
  - `tests/unit/test_config.py` - Config parsing, validation, defaults, XDG paths
  - `tests/unit/test_git_utils.py` - Git operations (mocked subprocess/GitPython)
  - `tests/unit/test_prompt_builder.py` - Prompt assembly logic with various inputs
  - `tests/unit/test_llm_client.py` - LLM client abstraction (mocked API responses)

- **Integration Tests Required**:
  - `tests/integration/test_cli.py` - End-to-end CLI flows for all user stories (P1-P3)

- **Coverage Target**: 85% minimum for all new modules (per constitution)
- **CI Blocking**: Yes - tests must pass before merge
- **Test Strategy**: Unit tests with mocks for external dependencies (git, LLM APIs, filesystem); integration tests with temporary git repos and mocked LLM responses

### UX Gate ✅

- **CLI Changes**: New main command with 5 flags
  - `gmuse` - Generate commit message (default behavior)
  - `gmuse --hint "text"` - Provide contextual hint
  - `gmuse --copy` - Copy to clipboard
  - `gmuse --model <name>` - Override model selection
  - `gmuse --format <style>` - Set format (freeform/conventional/gitmoji)
  - `gmuse --history-depth <n>` - Control history context

- **Help Text**: Complete `--help` output with examples and flag descriptions
- **Error Messages**: Actionable messages for all failure modes:
  - "Not a git repository — run this inside a repository folder."
  - "No staged changes found. Stage changes with `git add` or run `gmuse split` to plan commits from unstaged changes."
  - "No API key configured. Set `OPENAI_API_KEY` or configure provider in config.toml."
  - Network timeout: "Failed to reach LLM provider after 30s. Check network connection and retry."
  - Invalid config: "Error in config.toml line X: invalid TOML syntax."

- **Documentation Updates**:
  - `docs/source/user_guide/commit_messages.md` - New guide for message generation
  - `docs/source/getting_started/quickstart.md` - Add quickstart example
  - `docs/source/user_guide/configuration.md` - Document config.toml options
  - `README.md` - Add basic usage example

### Performance Gate ✅

- **Latency Target**: <10s for typical diffs (<1000 lines) with standard models
- **Token Management**:
  - Implement diff truncation at ~6000 tokens to stay under 8K total prompt size
  - Strategy: Keep function signatures, class definitions; truncate large repeated patterns
  - Fallback: If truncation insufficient, display error suggesting commit splitting

- **Network Timeout**: 30s default (configurable), with retry logic for transient failures
- **Memory**: Streaming not required for v1 (full diff loaded to memory)
- **Config Caching**: Load config.toml once per invocation (no hot-reload needed)
- **Mitigation**: Monitor token usage in logs when `GMUSE_DEBUG=1`, provide warnings before truncation

### Constitution Conformance Summary

| Gate | Status | Notes |
|------|--------|-------|
| Code Quality | ✅ PASS | Type hints + docstrings + Ruff + mypy enforced |
| Testing | ✅ PASS | Unit + integration tests, 85% coverage target |
| UX | ✅ PASS | Complete help text, actionable errors, docs updates |
| Performance | ✅ PASS | Token limits, timeouts, intelligent truncation |

**Conclusion**: All constitution gates pass. No violations requiring justification.

## Project Structure

### Documentation (this feature)

```text
specs/001-llm-commit-messages/
├── plan.md              # This file
├── research.md          # Phase 0 output: dependency research, design decisions
├── data-model.md        # Phase 1 output: entity relationships, data structures
├── quickstart.md        # Phase 1 output: getting started guide
├── contracts/           # Phase 1 output: API contracts (if needed)
│   └── prompt-templates.md  # LLM prompt structure documentation
├── checklists/
│   └── requirements.md  # Specification validation checklist (complete)
└── tasks.md             # Phase 2 output: implementation tasks (NOT created by plan)
```

### Source Code (repository root)

```text
src/gmuse/
├── __init__.py          # Existing: package version
├── py.typed             # Existing: type marker
├── cli/
│   ├── __init__.py      # Existing
│   └── main.py          # Modified: add generate command with flags
├── config.py            # New: config loading, validation, XDG paths
├── git_utils.py         # New: diff extraction, commit history, repo validation
├── prompt_builder.py    # New: prompt assembly, format handling
└── llm_client.py        # New: LiteLLM wrapper, provider detection

tests/
├── conftest.py          # Existing: shared fixtures
├── unit/
│   ├── test_config.py           # New: config module tests
│   ├── test_git_utils.py        # New: git operations tests
│   ├── test_prompt_builder.py  # New: prompt assembly tests
│   └── test_llm_client.py       # New: LLM client tests
└── integration/
    └── test_cli.py              # New: end-to-end CLI tests

docs/source/
├── user_guide/
│   ├── commit_messages.md       # New: comprehensive usage guide
│   └── configuration.md         # New: config reference
└── getting_started/
    └── quickstart.md            # Modified: add commit generation example
```

**Structure Decision**: Single project structure maintained (existing gmuse pattern). New modules added to `src/gmuse/` with clear separation of concerns: config management, git operations, prompt building, and LLM interaction. Tests mirror source structure with unit/integration split. This aligns with existing project organization and constitution requirements for modularity and testability.

## Complexity Tracking

> **No violations - this section is not required.**

All constitution gates pass without violations. The implementation follows standard patterns with appropriate modularization, testing, documentation, and performance considerations.

---

## Implementation Roadmap

This section provides a sequenced approach to implementation with references to detailed specifications.

### Phase 1: Foundation (P1 - Basic Generation)

**Goal**: Implement minimum viable product - generate commit messages from staged changes.

#### Step 1.1: Configuration Module
**File**: `src/gmuse/config.py`
**Reference**: [research.md § Configuration Management](research.md#3-configuration-management)
**Reference**: [data-model.md § UserConfig](data-model.md#5-userconfig)

Implementation tasks:
1. Create XDG path resolver (`get_config_path()`)
   - Handle `$XDG_CONFIG_HOME` or fallback to `~/.config`
   - Return: `Path` to `gmuse/config.toml`
2. Create config loader (`load_config()`)
   - Use `tomllib` (3.11+) or `tomli` (3.10) for parsing
   - Return: `dict` with defaults for missing keys
   - Handle: File not found (return defaults), invalid TOML (raise with line number)
3. Create config validator (`validate_config()`)
   - Check: Valid keys (model, copy_to_clipboard, history_depth, format)
   - Check: Valid types and ranges per [data-model.md § UserConfig validation rules](data-model.md#validation-rules-4)
   - Return: Validated config dict or raise `ConfigError`
4. Create config merger (`merge_config()`)
   - Priority: CLI args > config.toml > env vars > defaults
   - Return: Final config dict

**Test**: `tests/unit/test_config.py`
- Test XDG path resolution with various environments
- Test TOML parsing (valid, invalid, missing file)
- Test validation (valid configs, invalid keys, out-of-range values)
- Test priority merging

---

#### Step 1.2: Git Utilities Module
**File**: `src/gmuse/git_utils.py`
**Reference**: [research.md § Git Operations](research.md#2-git-operations)
**Reference**: [data-model.md § StagedDiff](data-model.md#2-stageddiff)
**Reference**: [data-model.md § CommitHistory](data-model.md#3-commithistory)

Implementation tasks:
1. Create repo validator (`is_git_repository()`)
   - Run: `git rev-parse --git-dir`
   - Return: `bool` (True if valid repo)
2. Create repo root getter (`get_repo_root()`)
   - Run: `git rev-parse --show-toplevel`
   - Return: `Path` to repo root or raise `NotAGitRepositoryError`
3. Create staged diff extractor (`get_staged_diff()`)
   - Run: `git diff --cached`
   - Parse: Extract file count, lines added/removed from diff stats
   - Return: `StagedDiff` object with raw_diff, files_changed, lines_added, lines_removed, hash
   - Handle: Empty diff (raise `NoStagedChangesError`)
4. Create commit history fetcher (`get_commit_history()`)
   - Run: `git log -n <depth> --format=%H|%s|%an|%at`
   - Parse: Split into CommitRecord objects
   - Return: `CommitHistory` object with commits list
   - Handle: First commit (empty history) gracefully
5. Create diff truncator (`truncate_diff()`)
   - Input: `StagedDiff`, `max_tokens` (default 6000)
   - Strategy: Keep file headers, function signatures; remove large bodies
   - See: [research.md § Token Management Strategy](research.md#7-token-management-strategy) for algorithm
   - Return: Truncated `StagedDiff` with `truncated=True` flag

**Test**: `tests/unit/test_git_utils.py`
- Test repo validation (valid repo, non-repo, git not in PATH)
- Test diff extraction (normal diff, empty, binary files)
- Test history fetching (multiple commits, first commit, depth limits)
- Test diff truncation (small diff, large diff, very large diff)

---

#### Step 1.3: LLM Client Module
**File**: `src/gmuse/llm_client.py`
**Reference**: [research.md § LLM Provider Integration](research.md#1-llm-provider-integration)

Implementation tasks:
1. Create provider detector (`detect_provider()`)
   - Check env vars: OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.
   - Return: Provider name string or None
2. Create model resolver (`resolve_model()`)
   - Input: model name (or None), provider name
   - Return: LiteLLM-compatible model string (e.g., "gpt-4", "claude-3-opus")
3. Create LLM client class (`LLMClient`)
   - Method: `generate(prompt: str, model: str, timeout: int) -> str`
   - Uses: `litellm.completion()` with error handling
   - Handle: Network errors, timeouts, rate limits, invalid API keys
   - Return: Generated message string
   - Raise: `LLMError` with actionable message (see [research.md § Error Handling](research.md#8-error-handling-patterns))
4. Create availability checker (`is_llm_available()`)
   - Check: litellm installed, API key present
   - Return: `bool`, error message if False

**Test**: `tests/unit/test_llm_client.py`
- Test provider detection (various env vars, none set)
- Test model resolution (explicit model, auto-detect, invalid)
- Test generation (mocked successful, network error, timeout, invalid key)
- Test availability check (installed, not installed, no key)

---

#### Step 1.4: Prompt Builder Module
**File**: `src/gmuse/prompt_builder.py`
**Reference**: [contracts/prompt-templates.md](contracts/prompt-templates.md)
**Reference**: [data-model.md § CommitMessage](data-model.md#1-commitmessage)

Implementation tasks:
1. Create system prompt constant (`SYSTEM_PROMPT`)
   - Use: [prompt-templates.md § Base System Prompt](contracts/prompt-templates.md#base-system-prompt)
2. Create context builder (`build_context()`)
   - Input: `StagedDiff`, `CommitHistory`, repo_instructions, user_hint
   - Format: Per [prompt-templates.md § Context Section Template](contracts/prompt-templates.md#context-section-template)
   - Omit: Empty optional sections
   - Return: Formatted context string
3. Create task prompt getters (one per format)
   - `get_freeform_task()`: [prompt-templates.md § Freeform Format](contracts/prompt-templates.md#freeform-format-default)
   - `get_conventional_task()`: [prompt-templates.md § Conventional Commits Format](contracts/prompt-templates.md#conventional-commits-format)
   - `get_gitmoji_task()`: [prompt-templates.md § Gitmoji Format](contracts/prompt-templates.md#gitmoji-format)
4. Create prompt assembler (`build_prompt()`)
   - Combine: SYSTEM_PROMPT + context + task (based on format)
   - Estimate: Token count (rough: chars / 4)
   - Truncate: If exceeds budget, truncate diff via `git_utils.truncate_diff()`
   - Return: Complete prompt string
5. Create message validator (`validate_message()`)
   - Check: Per [data-model.md § CommitMessage validation rules](data-model.md#validation-rules)
   - Format-specific: Regex for conventional, emoji check for gitmoji
   - Return: `bool` or raise `InvalidMessageError`

**Test**: `tests/unit/test_prompt_builder.py`
- Test context building (all fields, minimal fields, empty optionals)
- Test task prompts (each format)
- Test prompt assembly (normal, needs truncation, token budget)
- Test message validation (valid messages, invalid formats)

---

#### Step 1.5: CLI Command
**File**: `src/gmuse/cli/main.py` (modify existing)
**Reference**: [spec.md § User Story 1](spec.md#user-story-1---generate-basic-commit-message-priority-p1)

Implementation tasks:
1. Add generate command to Typer app
   - Command name: Default (runs when no subcommand)
   - Flags: `--hint`, `--copy`, `--model`, `--format`, `--history-depth`
   - Per: [plan.md § UX Gate CLI Changes](plan.md#ux-gate-)
2. Implement main flow:
   ```python
   def generate(
       hint: str | None = None,
       copy: bool = False,
       model: str | None = None,
       format: str = "freeform",
       history_depth: int | None = None,
   ):
       # 1. Load config (merge CLI args with config.toml)
       # 2. Validate git repository
       # 3. Get staged diff
       # 4. Get commit history
       # 5. Load .gmuse file if exists
       # 6. Build prompt
       # 7. Call LLM
       # 8. Validate message
       # 9. Output to stdout
       # 10. Optionally copy to clipboard
   ```
3. Add error handling for each error type
   - Use error messages from [plan.md § UX Gate Error Messages](plan.md#ux-gate-)
   - Exit codes: 0=success, 1=user error, 2=system error
4. Add help text
   - Include examples for each flag
   - Reference quickstart guide

**Test**: `tests/integration/test_cli.py`
- Test P1 user story acceptance scenarios (all 5)
- Use temporary git repos
- Mock LLM responses
- Verify exit codes, stdout output, error messages

---

### Phase 2: Enhancements (P2 - Hints, Clipboard, Formats)

#### Step 2.1: Repository Instructions
**Reference**: [spec.md § User Story 5](spec.md#user-story-5---repository-level-instructions-priority-p3)
**Reference**: [data-model.md § RepositoryInstructions](data-model.md#4-repositoryinstructions)

Implementation:
1. Add `.gmuse` file loader to `git_utils.py`
2. Integrate into `prompt_builder.build_context()`
3. Add tests for `.gmuse` presence/absence

#### Step 2.2: Clipboard Support
**Reference**: [spec.md § User Story 3](spec.md#user-story-3---copy-message-to-clipboard-priority-p2)
**Reference**: [research.md § Clipboard Operations](research.md#4-clipboard-operations)

Implementation:
1. Add pyperclip integration to CLI
2. Handle unavailable clipboard gracefully
3. Test on system with/without clipboard

---

### Phase 3: Documentation

#### Step 3.1: User Documentation
**Files**: `docs/source/user_guide/commit_messages.md`, `docs/source/user_guide/configuration.md`
**Reference**: [quickstart.md](quickstart.md)

Create comprehensive guides expanding on quickstart content.

#### Step 3.2: API Documentation
**Files**: All module docstrings

Ensure all public functions have Google-style docstrings with:
- Summary
- Args
- Returns
- Raises
- Examples

---

## Implementation Sequence Summary

```
Phase 1 (P1 - MVP):
  1.1 config.py      → 1.2 git_utils.py → 1.3 llm_client.py
                                        ↓
  1.4 prompt_builder.py ← (uses all above)
                     ↓
  1.5 cli/main.py (orchestrates everything)

Phase 2 (P2 - Enhancements):
  2.1 Repository instructions (.gmuse support)
  2.2 Clipboard support (pyperclip integration)

Phase 3 (Documentation):
  3.1 User docs
  3.2 API docs
```

**Key Dependencies**:
- `config.py` has no internal dependencies (can start here)
- `git_utils.py` has no internal dependencies (can start in parallel)
- `llm_client.py` has no internal dependencies (can start in parallel)
- `prompt_builder.py` depends on `git_utils` for `StagedDiff`/`CommitHistory` types
- `cli/main.py` depends on all above modules

**Testing Strategy**:
- Write unit tests alongside each module (TDD preferred)
- Write integration tests after Phase 1 is complete
- Achieve 85% coverage before moving to next phase
