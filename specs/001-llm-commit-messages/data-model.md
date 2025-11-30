# Data Model: LLM-Powered Commit Message Generator

**Feature**: 001-llm-commit-messages
**Date**: 2025-11-28
**Status**: Complete

## Overview

This document defines the data entities, their relationships, and state transitions for the commit message generation system. The model focuses on data structures used in runtime and persistence, without implementation details.

## Core Entities

### 1. CommitMessage

**Purpose**: Represents a generated commit message ready for use.

**Attributes**:
- `content` (string): The generated message text
- `format` (enum): Message style - "freeform", "conventional", or "gitmoji"
- `timestamp` (datetime): When the message was generated
- `model_used` (string): LLM model identifier (e.g., "gpt-4", "claude-3-opus")
- `truncated` (boolean): Whether the diff was truncated due to size

**Validation Rules**:
- `content` must not be empty
- `content` must not exceed 1000 characters (practical commit message limit)
- If `format` is "conventional", content must match pattern: `^(feat|fix|docs|style|refactor|test|chore)(\(.+\))?: .+`
- If `format` is "gitmoji", content must start with an emoji character

**Relationships**:
- Generated from one `StagedDiff`
- May optionally be influenced by `RepositoryInstructions`
- May optionally be influenced by `CommitHistory`

---

### 2. StagedDiff

**Purpose**: Represents the git diff of staged changes to be committed.

**Attributes**:
- `raw_diff` (string): Full output of `git diff --cached`
- `files_changed` (list[string]): Paths of modified files
- `lines_added` (integer): Total lines added across all files
- `lines_removed` (integer): Total lines removed across all files
- `hash` (string): SHA256 hash of raw_diff for deduplication
- `size_bytes` (integer): Size of raw_diff in bytes
- `truncated` (boolean): Whether diff was truncated for token limits

**Validation Rules**:
- `raw_diff` must not be empty
- `files_changed` must contain at least one file
- `lines_added` and `lines_removed` must be non-negative

**Derived Properties**:
- `total_changes` = lines_added + lines_removed
- `is_large` = total_changes > 1000

**State Transitions**:
- Created: Extract from git repository
- Truncated: If size exceeds token limits, apply intelligent truncation
- Hashed: Calculate SHA256 for deduplication

---

### 3. CommitHistory

**Purpose**: Collection of recent commit messages used for style context.

**Attributes**:
- `commits` (list[CommitRecord]): Ordered list of recent commits (newest first)
- `depth` (integer): Number of commits to include (default 5)
- `repository_path` (string): Absolute path to git repository root

**CommitRecord Sub-Entity**:
- `hash` (string): Git commit SHA
- `message` (string): Commit message text
- `author` (string): Commit author name
- `timestamp` (datetime): Commit timestamp

**Validation Rules**:
- `depth` must be between 0 and 50
- `commits` list length must not exceed `depth`
- If repository has fewer commits than `depth`, include all available

**Relationships**:
- Extracted from git repository identified by `repository_path`
- Provides style context for `CommitMessage` generation

---

### 4. RepositoryInstructions

**Purpose**: Project-level guidance for commit message generation from `.gmuse` file.

**Attributes**:
- `content` (string): Raw text content from `.gmuse` file
- `file_path` (string): Path to `.gmuse` file (typically repo root)
- `exists` (boolean): Whether `.gmuse` file is present

**Validation Rules**:
- If `exists` is true, `content` must not be empty
- `content` should be plain text (no binary data)
- Recommended max size: 1000 characters (to fit in prompt)

**Relationships**:
- One per repository (optional)
- Applied to all `CommitMessage` generations in that repository

**Example Content**:
```
Always reference Jira ticket numbers from branch names.
Use imperative mood (e.g., "Add feature" not "Added feature").
Mention breaking changes prominently.
```

---

### 5. UserConfig

**Purpose**: User-level configuration loaded from `$XDG_CONFIG_HOME/gmuse/config.toml`.

**Attributes**:
- `model` (string, optional): Default LLM model name
- `copy_to_clipboard` (boolean): Auto-copy messages to clipboard (default: false)
- `history_depth` (integer): Number of commits for style context (default: 5)
- `format` (enum): Default message format - "freeform", "conventional", "gitmoji" (default: "freeform")
- `timeout` (integer): Network timeout in seconds (default: 30)

**Validation Rules**:
- `model` must be a valid LiteLLM model identifier if provided
- `history_depth` must be between 0 and 50
- `format` must be one of: "freeform", "conventional", "gitmoji"
- `timeout` must be between 5 and 300 seconds

**Priority Resolution**:
1. CLI flags (highest priority)
2. `UserConfig` from config.toml
3. Environment variables (e.g., `GMUSE_MODEL`)
4. System defaults (lowest priority)

**Default Values**:
```toml
model = null  # Auto-detect from environment
copy_to_clipboard = false
history_depth = 5
format = "freeform"
timeout = 30
```

---

## Entity Relationships Diagram

```
┌─────────────────┐
│   UserConfig    │ (config.toml)
└────────┬────────┘
         │
         │ configures
         ▼
┌─────────────────────────────────────────────────┐
│              Message Generation                  │
│                   (Runtime)                      │
└─────────────────────────────────────────────────┘
         │
         │ uses
         ▼
┌─────────────────┐     ┌──────────────────┐
│   StagedDiff    │────▶│ CommitMessage    │
└─────────────────┘     └──────────────────┘
         │                      ▲
         │                      │
         ▼                      │
┌─────────────────┐            │
│ CommitHistory   │────────────┘
└─────────────────┘
         ▲
         │
         │              ┌──────────────────────┐
         └──────────────│ Repository Context   │
                        │  (git repo root)     │
                        └──────────────────────┘
                                 ▲
                                 │
                        ┌────────┴────────┐
                        │ Repository      │
                        │ Instructions    │
                        │  (.gmuse file)  │
                        └─────────────────┘
```

## Data Flow Sequence

### Primary Flow: Generate Commit Message

1. **Load Configuration**: Read `UserConfig` from config.toml + merge CLI flags
2. **Validate Repository**: Check git repository exists and has staged changes
3. **Extract Context**:
   - Create `StagedDiff` from `git diff --cached`
   - Create `CommitHistory` from `git log`
   - Load `RepositoryInstructions` from `.gmuse` if exists
4. **Build Prompt**: Combine all context into structured prompt
5. **Call LLM**: Send prompt to provider, receive response
6. **Create CommitMessage**: Parse LLM response, validate format
7. **Output**: Print message to STDOUT, optionally copy to clipboard

## Storage Locations

| Entity | Storage Location | Format | Persistence |
|--------|------------------|--------|-------------|
| CommitMessage | Runtime only (STDOUT) | String | Transient |
| StagedDiff | Runtime only | String | Transient |
| CommitHistory | Runtime only (from git) | List | Transient |
| RepositoryInstructions | `<repo_root>/.gmuse` | Plain text | Git-tracked |
| UserConfig | `$XDG_CONFIG_HOME/gmuse/config.toml` | TOML | Persistent |

## Privacy & Security Considerations

- **API keys**: Never stored, only read from environment variables
- **XDG compliance**: Standard paths enable user control over data location

## Extension Points for Future Versions

- **v1.1**: Add commit splitting entities (hunk-level analysis)
- **v1.2**: Add user-level instructions file (similar to .gmuse but global)
- **v2.0**: Add message templates (custom format definitions)
