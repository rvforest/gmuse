# Research: LLM-Powered Commit Message Generator

**Feature**: 001-llm-commit-messages  
**Date**: 2025-11-28  
**Status**: Complete

## Purpose

This document resolves technical unknowns and establishes design decisions for implementing LLM-powered commit message generation. All research findings inform the implementation plan and data model.

## Research Areas

### 1. LLM Provider Integration

**Decision**: Use LiteLLM as unified provider interface

**Rationale**:
- Supports 100+ LLM providers (OpenAI, Anthropic, Cohere, Azure, etc.) with unified API
- Auto-detects provider from environment variables (OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.)
- Handles provider-specific quirks (rate limiting, token counting, error codes)
- MIT licensed, actively maintained
- Zero-config first-time experience aligns with spec requirements

**Alternatives Considered**:
- **Direct OpenAI SDK**: Limited to OpenAI only, requires users to choose provider upfront
- **Direct Anthropic SDK**: Same limitation as OpenAI
- **Custom abstraction**: High maintenance burden, would require implementing rate limiting, retries, etc.

**Implementation Notes**:
- Install as optional dependency: `pip install gmuse[llm]` includes litellm
- Fallback: If litellm not installed, show clear error with installation instructions
- Model name format: Provider-agnostic strings like "gpt-4", "claude-3-opus" (litellm handles routing)

---

### 2. Git Operations

**Decision**: Use subprocess with git CLI (not GitPython)

**Rationale**:
- Git CLI is universally available on systems where users commit code
- subprocess is stdlib (no dependencies)
- Simple operations (diff, log) don't require complex object model
- GitPython adds 10+ dependencies and increases installation size
- Better error messages by passing through git's native errors

**Alternatives Considered**:
- **GitPython**: Full-featured but heavyweight; overkill for reading diffs/logs
- **pygit2**: Requires libgit2 compiled library, complicates installation

**Implementation Notes**:
- Operations needed: `git diff --cached`, `git log -n <depth> --format=%s`, `git rev-parse --git-dir`, `git rev-parse --show-toplevel`
- Error handling: Check `git` exists in PATH, validate return codes, parse stderr
- Platform compatibility: Use `subprocess.run()` with `capture_output=True`, handle Windows paths

---

### 3. Configuration Management

**Decision**: Use tomllib (stdlib 3.11+) with tomli backport for 3.10

**Rationale**:
- TOML is standard for Python projects (pyproject.toml familiarity)
- `tomllib` in stdlib 3.11+, `tomli` for 3.10 (read-only, pure Python)
- XDG Base Directory compliance for config location
- Simple key-value structure matches requirements

**Alternatives Considered**:
- **YAML**: Requires PyYAML dependency, more complex syntax
- **JSON**: No comments support, less human-friendly
- **INI**: Limited type support, outdated format

**Implementation Notes**:
- Config path: `$XDG_CONFIG_HOME/gmuse/config.toml` (fallback: `~/.config/gmuse/config.toml`)
- Schema validation: Define allowed keys, types, and defaults
- Priority: CLI flags > config.toml > environment variables > defaults
- Graceful degradation: If config missing or invalid, use defaults and show warning

**Config Schema**:
```toml
# Optional: Override default model
model = "gpt-4"

# Optional: Auto-copy to clipboard
copy_to_clipboard = false

# Optional: Enable learning from edits
learning_enabled = false

# Optional: Number of recent commits for style context
history_depth = 5

# Optional: Commit message format style
format = "freeform"  # Options: "freeform", "conventional", "gitmoji"
```

---

### 4. Clipboard Operations

**Decision**: Use pyperclip with graceful degradation

**Rationale**:
- Cross-platform clipboard support (Linux, macOS, Windows)
- Handles platform-specific clipboard mechanisms (xclip/xsel/pbcopy/etc.)
- Small, focused library (1 file, ~200 lines)
- MIT licensed

**Alternatives Considered**:
- **Platform-specific code**: Would require maintaining Linux/macOS/Windows implementations
- **tkinter**: Heavyweight, requires X server on Linux

**Implementation Notes**:
- Install as optional dependency: `pip install gmuse[clipboard]` includes pyperclip
- Graceful fallback: If pyperclip not available or clipboard access fails, print warning and continue
- Error handling: Catch `pyperclip.PyperclipException` for systems without clipboard support

---

### 5. Learning Data Storage

**Decision**: JSONL (JSON Lines) format in `$XDG_DATA_HOME/gmuse/history.jsonl`

**Rationale**:
- Append-only format ideal for logging events
- Each line is valid JSON (easy to parse, inspect manually)
- No database dependencies
- Standard format for ML/logging data
- Easy to export, backup, or delete

**Alternatives Considered**:
- **SQLite**: Overkill for simple append-only log, adds complexity
- **Single JSON file**: Requires full file rewrite on each append, race conditions
- **CSV**: Limited type support, harder to evolve schema

**Implementation Notes**:
- Record structure:
  ```json
  {
    "timestamp": "2025-11-28T10:30:00Z",
    "repo_id": "sha256_of_repo_root_path",
    "generated_message": "Add user authentication",
    "final_message": "feat(auth): implement JWT-based authentication",
    "diff_hash": "sha256_of_staged_diff",
    "model_used": "gpt-4",
    "format": "conventional"
  }
  ```
- Repo identification: SHA256 hash of absolute repo root path (stable, privacy-preserving)
- Loading strategy: Read last N lines (default 10) for current repo_id only
- Privacy: Store minimal data, no raw code diffs

---

### 6. Prompt Design Patterns

**Decision**: Structured prompt with system + context + task sections

**Rationale**:
- Clear separation of concerns improves LLM understanding
- System prompt sets role and constraints
- Context section provides diff, history, instructions
- Task section specifies format and output requirements
- Best practice from LLM prompting research (Anthropic, OpenAI guidelines)

**Prompt Structure**:
```
SYSTEM:
You are a commit message generator. Generate clear, concise commit messages based on staged changes.

CONTEXT:
Repository: <repo_name>
Recent commits for style reference:
- <commit1>
- <commit2>
...

Repository instructions: <.gmuse file content>
User hint: <--hint value>

Staged changes:
<git diff --cached output>

TASK:
Generate a commit message in <format> style.
- Freeform: Natural language, focus on clarity
- Conventional: type(scope): description format
- Gitmoji: Emoji prefix + description

Output only the commit message, no explanations.
```

**Implementation Notes**:
- Token budget: Reserve ~2000 tokens for system/task, ~6000 for context (diff + history)
- Diff truncation: If diff exceeds budget, keep file headers, function signatures, remove large repetitions
- Few-shot learning: Include generated->final pairs from learning history when available
- Format-specific instructions: Inject format rules into task section based on `--format` flag

---

### 7. Token Management Strategy

**Decision**: Intelligent diff truncation with preservation of semantic structure

**Rationale**:
- Large diffs (>5000 lines) exceed most model context windows
- Removing entire sections risks losing important context
- Preserving structure (class/function definitions) maintains clarity
- Warnings inform user when truncation occurs

**Truncation Algorithm**:
1. Count lines in diff
2. If <1000 lines: No truncation
3. If 1000-5000 lines: Remove large repeated blocks (auto-generated code, minified files)
4. If >5000 lines: 
   - Keep file headers (+++/--- lines)
   - Keep function/class signature lines
   - Truncate function bodies to first 10 lines
   - Show summary: "X files changed, Y lines added, Z lines deleted"
   - Warn user: "Large diff truncated. Consider splitting commit."

**Implementation Notes**:
- Use regex to identify function/class definitions (Python, JS, etc.)
- Detect auto-generated files by header comments or filenames (*.min.js, *.generated.*, etc.)
- Provide `GMUSE_DEBUG=1` flag to log full diff token count

---

### 8. Error Handling Patterns

**Decision**: Actionable error messages with remediation steps

**Rationale**:
- Constitution requires 95% self-service issue resolution
- Clear error messages reduce support burden
- Actionable advice helps users fix problems independently

**Error Categories & Messages**:

1. **Not a git repository**:
   ```
   Error: Not a git repository
   
   Run this command inside a git repository folder.
   To initialize a new repository: git init
   ```

2. **No staged changes**:
   ```
   Error: No staged changes found
   
   Stage your changes first:
     git add <files>
   
   Or use 'gmuse split' to plan commits from unstaged changes (v1.1+).
   ```

3. **No API key**:
   ```
   Error: No LLM provider API key configured
   
   Set an environment variable for your provider:
     export OPENAI_API_KEY="sk-..."
     export ANTHROPIC_API_KEY="sk-ant-..."
   
   Or configure in config.toml:
     model = "gpt-4"
   
   Config location: ~/.config/gmuse/config.toml
   ```

4. **Network failure**:
   ```
   Error: Failed to reach LLM provider
   
   Check your network connection and try again.
   If the problem persists, the provider may be experiencing issues.
   
   Timeout after 30 seconds. Increase with environment variable:
     export GMUSE_TIMEOUT=60
   ```

5. **Invalid config**:
   ```
   Error: Invalid configuration file
   
   File: ~/.config/gmuse/config.toml
   Line 5: Unknown key 'invalid_option'
   
   Valid keys: model, copy_to_clipboard, learning_enabled, history_depth, format
   See documentation: https://gmuse.readthedocs.io/config
   ```

**Implementation Notes**:
- Use `typer.echo()` with `err=True` for errors
- Exit codes: 0=success, 1=user error, 2=system error
- Colored output with typer.style() for errors (red) and warnings (yellow)

---

## Summary of Key Decisions

| Decision Area | Choice | Rationale |
|---------------|--------|-----------|
| LLM Provider | LiteLLM | Unified interface, auto-detection, 100+ providers |
| Git Operations | subprocess + git CLI | Universal availability, no dependencies |
| Configuration | tomllib/tomli + TOML | Stdlib, human-friendly, XDG compliant |
| Clipboard | pyperclip (optional) | Cross-platform, graceful degradation |
| Learning Storage | JSONL | Append-only, standard format, no DB needed |
| Prompt Design | Structured (system/context/task) | Clear sections, best practice pattern |
| Token Management | Intelligent truncation | Preserve structure, warn user |
| Error Handling | Actionable messages | 95% self-service resolution target |

## Follow-up Actions

1. Create data model documenting entity relationships
2. Design prompt templates for each format (freeform, conventional, gitmoji)
3. Define test fixtures (sample diffs, config files, learning history)
4. Create quickstart guide with example workflows
5. Update agent context with new technology decisions
