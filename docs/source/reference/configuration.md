# Configuration Reference

Comprehensive reference of all configuration options and environment variables that affect gmuse's behavior. For quick setup steps and common tasks, see the How‑to: [Configure gmuse](../how_to/configuration.md).

## Configuration Hierarchy

gmuse loads configuration from multiple sources with the following priority (highest to lowest):

1. **CLI flags** — Command-line options passed to `gmuse msg`
2. **User configuration file** — Persistent user preferences
3. **Environment variables** — `GMUSE_*` variables
4. **Defaults** — Built-in fallback values

## User Configuration File

gmuse loads persistent user-level configuration from:

**Location:** `$XDG_CONFIG_HOME/gmuse/config.toml`
**Fallback:** `~/.config/gmuse/config.toml`

**Format:** TOML with top-level keys (no section headers needed)

**Example:**
```toml
model = "gpt-4o-mini"
provider = "openai"
format = "conventional"
history_depth = 10
copy_to_clipboard = false
timeout = 60
```

> **Note:** This is separate from repository-level instructions (see [](#repository-instructions) below).

## Configuration Options

### provider

**Type:** string
**Default:** `null` (auto-detected)
**Valid values:** `"openai"`, `"anthropic"`, `"gemini"`, `"cohere"`, `"azure"`, `"bedrock"`, `"huggingface"`

LLM provider to use for generation. If not specified, gmuse auto-detects the provider based on available API keys.

```toml
provider = "openai"
```

Run `gmuse info` to see which provider was detected.

**Provider API Keys:** gmuse detects providers based on these environment variables:

| Variable | Provider |
|----------|----------|
| `OPENAI_API_KEY` | OpenAI |
| `ANTHROPIC_API_KEY` | Anthropic |
| `GEMINI_API_KEY` or `GOOGLE_API_KEY` | Google Gemini |
| `COHERE_API_KEY` | Cohere |
| `AZURE_API_KEY` | Azure OpenAI |

### model

**Type:** string
**Default:** `null` (auto-detected based on provider)
**Environment variable:** `GMUSE_MODEL`

LLM model identifier to use for generation. If not specified, gmuse selects a default model based on the detected provider:

- `openai` → `gpt-4o-mini`
- `anthropic` → `claude-3-5-sonnet-20241022`
- `gemini` → `gemini/gemini-flash-lite-latest`
- `cohere` → `command`
- `azure` → `gpt-4o`

**For providers without default models** (such as `bedrock` and `huggingface`), you **must** specify a model explicitly using the `model` configuration option, `GMUSE_MODEL` environment variable, or the `--model` CLI flag. Otherwise, gmuse will raise an error with instructions.

```toml
model = "gpt-4o"
```

### format

**Type:** string
**Default:** `"freeform"`
**Valid values:** `"freeform"`, `"conventional"`, `"gitmoji"`
**CLI flag:** `--format`, `-f`
**Environment variable:** `GMUSE_FORMAT`

Commit message format style:

- `freeform` — Natural language messages with no specific structure
- `conventional` — [Conventional Commits](https://www.conventionalcommits.org/) format (`type(scope): description`)
- `gitmoji` — Messages prefixed with relevant emoji

```toml
format = "conventional"
```

### history_depth

**Type:** integer
**Default:** `5`
**Valid range:** `0` to `50`
**CLI flag:** `--history-depth`
**Environment variable:** `GMUSE_HISTORY_DEPTH`

Number of recent commits to include in the prompt as style examples. Set to `0` to disable commit history context.

```toml
history_depth = 10
```

### timeout

**Type:** integer (seconds)
**Default:** `30`
**Valid range:** `5` to `300`
**Environment variable:** `GMUSE_TIMEOUT`

Request timeout for LLM API calls in seconds.

```toml
timeout = 60
```

### copy_to_clipboard

**Type:** boolean
**Default:** `false`
**CLI flag:** `--copy`, `-c`
**Environment variable:** `GMUSE_COPY` (accepts `"1"`, `"true"`, `"yes"`)

Automatically copy generated commit messages to the system clipboard.

```toml
copy_to_clipboard = true
```

**Requirements:** Requires the optional `gmuse[clipboard]` extra (provides `pyperclip`) and a system clipboard utility (`pbcopy`, `xclip`, or `wl-copy`).

### learning_enabled

**Type:** boolean
**Default:** `false`
**Environment variable:** `GMUSE_LEARNING` (accepts `"1"`, `"true"`, `"yes"`)

**Status:** Experimental (not yet implemented)

When enabled, gmuse will learn from your commit message edits to improve future suggestions. Learning data will be stored in `$XDG_DATA_HOME/gmuse/history.jsonl`.

```toml
learning_enabled = false
```

> **Privacy note:** Learning is opt-in and disabled by default. Learning data is stored locally only.

### log_file

**Type:** string (file path)
**Default:** `null`
**Environment variable:** `GMUSE_LOG_FILE`

Optional path to write debug logs. If not specified, logs are written to stderr. Supports tilde (`~`) expansion.

```toml
log_file = "~/.cache/gmuse/debug.log"
```

**Environment variable:** Set `GMUSE_DEBUG=1` to enable detailed logging for troubleshooting.

> **Security warning:** When `GMUSE_DEBUG=1` is enabled, prompts, diffs, and hints may appear in logs. Avoid enabling debug mode in sensitive environments. API keys are always redacted in logs.

## LLM Generation Parameters

The following parameters control LLM behavior but are **not directly configurable** through gmuse configuration. They are internal defaults used by the LLM client:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `temperature` | `0.7` | Controls randomness (0.0 = deterministic, 1.0 = creative) |
| `max_tokens` | `500` | Maximum response length |

These values are hardcoded in `gmuse.llm.LLMClient.generate()`. To adjust them, you would need to modify provider-specific settings or the gmuse source code.

> **Tip:** For more deterministic outputs, choose models known for consistent behavior (e.g., `gpt-4o-mini`) rather than creative models.

## Repository Instructions

In addition to user-level configuration, gmuse supports **repository-level instructions** that are committed to the project and shared with all contributors.

**Location:** `.gmuse` file in repository root

The `.gmuse` file contains plain text instructions that are injected directly into the LLM prompt. This is useful for team-wide conventions like:

- "Always reference a Jira ticket ID"
- "Keep subject lines under 50 characters"
- "Use past tense for commit messages"

**Example `.gmuse` file:**
```
All commit messages must reference a ticket ID in the format [PROJ-123].
Keep subject lines under 50 characters.
```

> **Note:** The `.gmuse` file is for prompt instructions, not configuration options. Configuration options must be in the user config file.


## See also

* How‑to: [Configure gmuse](../how_to/configuration.md)
* How it Works: [](../explanation/how_it_works.md#generation-parameters)
* Troubleshooting: [Troubleshooting guide](../how_to/troubleshooting.md)
