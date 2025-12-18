# Data Model: zsh completions for gmuse

## Entities

### CompletionRequest
Represents the input context for generating a commit message.

| Field | Type | Description |
|-------|------|-------------|
| `staged_diff` | `str` | The staged changes (`git diff --staged`). |
| `config` | `dict` | Configuration values (timeout, etc.). |

### CompletionResponse
Represents the output from the runtime helper.

| Field | Type | Description |
|-------|------|-------------|
| `suggestion` | `str` | The generated commit message. |
| `status` | `enum` | `ok`, `timeout`, `offline`, `no_staged_changes`, `error`. |
| `metadata` | `dict` | Additional info (e.g., `truncated`, `elapsed_ms`). |

### CacheEntry
Represents the cached suggestion in Zsh.

| Field | Type | Description |
|-------|------|-------------|
| `suggestion` | `str` | The cached commit message. |
| `timestamp` | `int` | Unix timestamp of when the cache was created. |
