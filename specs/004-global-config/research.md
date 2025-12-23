# Research: Global Config CLI

**Feature**: 004-global-config
**Date**: 2025-12-23
**Status**: Complete

## Research Questions

### 1. TOML Writing Library Selection

**Question**: Which library should be used for writing TOML files while preserving comments and formatting?

**Research**:

| Library | Pros | Cons |
|---------|------|------|
| `tomlkit` | Preserves comments, style-preserving, actively maintained, used by Poetry | Additional dependency |
| `tomli_w` | Minimal, fast, from same author as tomli | Does not preserve comments/formatting |
| Manual string building | No dependencies | Error-prone, no validation, loses formatting |

**Decision**: Use `tomlkit` for TOML writing.

**Rationale**:
- Preserves existing comments and formatting in user's config file (important for UX)
- Actively maintained (used by Poetry, PDM, and other major tools)
- Provides both read and write capabilities (can replace tomllib for write cases)
- Round-trip editing is a core feature

**Alternatives Rejected**:
- `tomli_w`: Does not preserve comments, which could frustrate users who document their config
- Manual building: Too error-prone and loses user's file structure

### 2. CLI Command Structure

**Question**: Should config commands be `gmuse config view/set` or `gmuse global-config view/set`?

**Research**:
- Existing CLI uses `gmuse msg`, `gmuse info`, `gmuse git-completions`
- Git uses `git config` for configuration (precedent)
- Typer supports subcommand groups via `add_typer()`
- Spec mentions "global-config" but also references consistency with git conventions

**Decision**: Use `gmuse config view` and `gmuse config set` (without "global-" prefix).

**Rationale**:
- Matches git's `git config` command pattern (UX consistency)
- Shorter and more memorable
- The subcommands can clarify scope (e.g., `--global` flag in future if per-repo config added)
- Avoids redundancy since gmuse currently only has global config

**Alternatives Rejected**:
- `gmuse global-config`: Verbose, unlike git convention
- Top-level commands (`gmuse view-config`): Doesn't group related functionality

### 3. Key Validation Approach

**Question**: How should config keys be validated?

**Research**:
- Existing `config.py` has `DEFAULTS` dict with all known keys
- `validate_config()` already warns about unknown keys
- Spec requires rejecting unknown keys (FR-012)

**Decision**: Define `ALLOWED_CONFIG_KEYS` as `frozenset(DEFAULTS.keys())` and validate against it.

**Rationale**:
- Single source of truth (derived from DEFAULTS)
- Easy to maintain as new config options are added
- Consistent with existing validation patterns

**Implementation**:
```python
ALLOWED_CONFIG_KEYS: Final[frozenset[str]] = frozenset(DEFAULTS.keys())
```

### 4. Value Parsing and Validation

**Question**: How should user-provided string values be converted to appropriate types?

**Research**:
- Users will input values as strings via CLI (e.g., `gmuse config set history_depth 10`)
- Config values have different types: string, int, float, bool
- Existing validation functions handle type checking

**Decision**: Infer expected type from `DEFAULTS` and parse accordingly.

**Rationale**:
- `DEFAULTS` already defines the canonical type for each key
- Type inference keeps the CLI simple (no explicit type flags)
- Validation functions already exist for each type

**Type Conversion Rules**:
| Default Type | Parsing Rule |
|--------------|--------------|
| `bool` | `"true"`, `"1"`, `"yes"` → True; `"false"`, `"0"`, `"no"` → False |
| `int` | `int(value)` |
| `float` | `float(value)` |
| `str` | Use as-is |
| `None` | Treat as optional string |

### 5. Credential/Secret Handling

**Question**: Which config keys should be blocked from being stored?

**Research**:
- Constitution requires: "The project MUST NOT store API keys or secrets in the repository"
- Spec FR-007: "The set command MUST NOT store credentials or API keys in global config"
- Current credentials are env-based: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.
- No credential fields exist in `DEFAULTS`

**Decision**: No special blocking needed; credential keys don't exist in `DEFAULTS`.

**Rationale**:
- `DEFAULTS` doesn't include any API keys or secrets
- Key validation against `DEFAULTS` automatically excludes credential-like keys
- If future versions add credential fields, they should be explicitly blocked

### 6. File Creation and Atomic Writes

**Question**: How should the config file be created/updated safely?

**Research**:
- Spec FR-009: Create parent directories if missing
- Spec edge case: Concurrent edits should not corrupt file
- `pathlib.Path.mkdir(parents=True, exist_ok=True)` handles directory creation
- `tomlkit` operates on document objects, not direct file writes

**Decision**: Use atomic write pattern with temp file and rename.

**Rationale**:
- Atomic writes prevent corruption from interrupted writes or crashes
- Standard pattern for config file updates
- `tempfile` + `os.replace()` provides atomic semantics on most platforms

**Implementation Approach**:
```python
def save_config(config_path: Path, document: TOMLDocument) -> None:
    """Atomically save config to file."""
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode='w',
        dir=config_path.parent,
        delete=False,
        suffix='.tmp'
    ) as tmp:
        tmp.write(tomlkit.dumps(document))
        tmp_path = Path(tmp.name)
    os.replace(tmp_path, config_path)  # Atomic on POSIX
```

### 7. View Output Format

**Question**: How should `config view` display configuration?

**Research**:
- Spec FR-002: Show file contents + merged summary with override highlights
- Spec FR-013: Highlight when env vars override file values
- Current `gmuse info` uses `typer.echo()` for output

**Decision**: Two-section output: raw file contents, then merged summary table.

**Rationale**:
- Shows exactly what's in the file (transparency)
- Shows effective values with override sources (clarity)
- Matches spec requirements for override visibility

**Output Format**:
```
Global config file: ~/.config/gmuse/config.toml

--- File Contents ---
model = "gpt-4"
format = "conventional"
history_depth = 10

--- Effective Configuration ---
Key               Value                Source
─────────────────────────────────────────────────
model             gpt-4                config file
format            conventional         config file
history_depth     10                   config file
timeout           30                   default
copy_to_clipboard false                default
include_branch    true                 env (GMUSE_INCLUDE_BRANCH) ← overrides file
```

## Dependencies to Add

```toml
# pyproject.toml
dependencies = [
    # ... existing
    "tomlkit>=0.12.0",  # NEW: TOML reading/writing with comment preservation
]
```

## Summary

All research questions resolved. Ready for Phase 1 design.

| Question | Decision |
|----------|----------|
| TOML writing library | `tomlkit` (preserves comments) |
| CLI structure | `gmuse config view/set` |
| Key validation | Against `DEFAULTS.keys()` |
| Value parsing | Infer type from `DEFAULTS` |
| Credential handling | Automatically excluded (not in DEFAULTS) |
| File operations | Atomic writes with temp file |
| View output | File contents + merged summary with overrides |
