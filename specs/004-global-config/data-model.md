# Data Model: Global Config CLI

**Feature**: 004-global-config
**Date**: 2025-12-23

## Entities

### ConfigKey

Represents a valid configuration option name.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| name | `str` | Configuration key identifier | Must be in `ALLOWED_CONFIG_KEYS` |
| value_type | `type` | Expected Python type | Inferred from `DEFAULTS[name]` |
| description | `str` | Human-readable description | From docstrings/docs |

**Derived From**: `DEFAULTS` dictionary in `config.py`

**Current Keys** (from existing codebase):
- `model`: `Optional[str]` - LLM model name
- `provider`: `Optional[str]` - LLM provider (openai, anthropic, etc.)
- `format`: `str` - Message format (freeform, conventional, gitmoji)
- `history_depth`: `int` - Recent commits for context (0-50)
- `timeout`: `int` - API timeout seconds (5-300)
- `temperature`: `float` - LLM sampling temperature (0.0-2.0)
- `max_tokens`: `int` - Max tokens in response (1-100000)
- `max_diff_bytes`: `int` - Max diff size (1000-10000000)
- `max_message_length`: `int` - Max message length (10-10000)
- `chars_per_token`: `int` - Token estimation heuristic (1-10)
- `copy_to_clipboard`: `bool` - Auto-copy to clipboard
- `learning_enabled`: `bool` - Enable learning mode
- `include_branch`: `bool` - Include branch context
- `branch_max_length`: `int` - Branch summary max length (20-200)
- `log_file`: `Optional[str]` - Debug log file path

### ConfigValue

Represents a parsed and validated configuration value.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| raw | `str` | User-provided string | From CLI argument |
| parsed | `Any` | Type-converted value | Matches `ConfigKey.value_type` |
| validated | `bool` | Passed validation | True after `validate_config()` |

**Type Conversion Rules**:

| Target Type | Accepted Inputs | Conversion |
|-------------|-----------------|------------|
| `bool` | `"true"`, `"1"`, `"yes"`, `"false"`, `"0"`, `"no"` | Case-insensitive |
| `int` | Numeric string | `int(value)` |
| `float` | Numeric string | `float(value)` |
| `str` | Any string | Direct use |
| `Optional[str]` | Any string or `"null"`, `"none"` | `None` for null keywords |

### ConfigSource

Enum representing the origin of a configuration value.

| Value | Description |
|-------|-------------|
| `DEFAULT` | From `DEFAULTS` constant |
| `CONFIG_FILE` | From `~/.config/gmuse/config.toml` |
| `ENVIRONMENT` | From `GMUSE_*` environment variable |
| `CLI` | From command-line flag (not applicable for config commands) |

### EffectiveConfig

Represents the merged configuration with source tracking.

| Field | Type | Description |
|-------|------|-------------|
| key | `str` | Configuration key name |
| value | `Any` | Effective value after merging |
| source | `ConfigSource` | Where the value came from |
| overridden_by | `Optional[ConfigSource]` | Higher-priority source that overrides file |

## Relationships

```
┌─────────────────┐     validates     ┌─────────────────┐
│   ConfigKey     │─────────────────▶│   ConfigValue   │
│                 │                   │                 │
│ - name          │                   │ - raw           │
│ - value_type    │                   │ - parsed        │
│ - description   │                   │ - validated     │
└─────────────────┘                   └─────────────────┘
        │
        │ defines allowed keys
        ▼
┌─────────────────────────────────────────────────────────┐
│                   GlobalConfig                          │
│  ~/.config/gmuse/config.toml                            │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ model=gpt-4  │  │ format=conv  │  │ history=10   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
        │
        │ merges with
        ▼
┌─────────────────────────────────────────────────────────┐
│                  EffectiveConfig                        │
│                                                         │
│  DEFAULTS ← ENV VARS ← CONFIG FILE ← CLI FLAGS          │
│  (lowest)                              (highest)        │
│                                                         │
│  Each key tracked with source + override indicators     │
└─────────────────────────────────────────────────────────┘
```

## State Transitions

### Config Set Flow

```
    User Input           Validation          Persistence
    ┌──────────┐       ┌──────────┐        ┌──────────┐
    │ key=val  │──────▶│ validate │───────▶│  write   │
    └──────────┘       │   key    │        │   file   │
         │             │   value  │        └────┬─────┘
         │             └────┬─────┘             │
         │                  │                   │
         │ INVALID          │ VALID             │ SUCCESS
         ▼                  ▼                   ▼
    ┌──────────┐       ┌──────────┐        ┌──────────┐
    │  ERROR   │       │  parse   │        │ confirm  │
    │  exit 1  │       │  value   │        │  exit 0  │
    └──────────┘       └──────────┘        └──────────┘
```

### Config View Flow

```
    ┌──────────────┐
    │ Check file   │
    │   exists?    │
    └──────┬───────┘
           │
     ┌─────┴─────┐
     │           │
   NO│         YES│
     ▼           ▼
┌─────────┐  ┌─────────┐
│ Show    │  │ Read    │
│ "no     │  │ file    │
│ config" │  │ contents│
└────┬────┘  └────┬────┘
     │            │
     │            ▼
     │       ┌─────────┐
     │       │ Merge   │
     │       │ sources │
     │       └────┬────┘
     │            │
     ▼            ▼
┌─────────────────────┐
│ Display effective   │
│ config with sources │
│ and override flags  │
└─────────────────────┘
```

## Validation Rules

### Key Validation
- Key MUST exist in `ALLOWED_CONFIG_KEYS`
- Error message: `Unknown configuration key: '{key}'. Valid keys: {sorted_keys}`

### Value Validation (per type)

| Key Type | Validation | Error Message |
|----------|------------|---------------|
| `format` | Must be in `VALID_FORMATS` | `Invalid format: '{value}'. Must be one of: freeform, conventional, gitmoji` |
| `provider` | Must be in `VALID_PROVIDERS` or null | `Invalid provider: '{value}'. Must be one of: {providers}` |
| `history_depth` | 0 ≤ value ≤ 50 | `history_depth must be between 0 and 50, got {value}` |
| `timeout` | 5 ≤ value ≤ 300 | `timeout must be between 5 and 300 seconds, got {value}` |
| `temperature` | 0.0 ≤ value ≤ 2.0 | `temperature must be between 0.0 and 2.0, got {value}` |
| `bool` fields | true/false/1/0/yes/no | `{key} must be a boolean (true/false), got '{value}'` |

### Parse Error Messages
- Integer parse failure: `Cannot parse '{value}' as integer for {key}`
- Float parse failure: `Cannot parse '{value}' as number for {key}`

## File Schema

```toml
# ~/.config/gmuse/config.toml
# Global gmuse configuration

# LLM settings
model = "gpt-4o-mini"
provider = "openai"
temperature = 0.7
max_tokens = 500
timeout = 30

# Message formatting
format = "conventional"
max_message_length = 1000

# Context settings
history_depth = 10
include_branch = false
branch_max_length = 60

# Diff handling
max_diff_bytes = 20000
chars_per_token = 4

# Behavior
copy_to_clipboard = false
learning_enabled = false

# Debugging (optional)
# log_file = "/tmp/gmuse.log"
```
