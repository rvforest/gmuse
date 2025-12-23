# Quickstart: Global Config CLI

**Feature**: 004-global-config
**Date**: 2025-12-23

## Overview

The `gmuse config` commands let you view and modify your global configuration without manually editing files.

## Prerequisites

- gmuse installed (`pip install gmuse`)
- Shell access

## Quick Examples

### View your current configuration

```bash
gmuse config view
```

**Example output:**
```
Global config file: /home/user/.config/gmuse/config.toml

--- File Contents ---
model = "gpt-4o-mini"
format = "conventional"

--- Effective Configuration ---
Key                 Value                  Source
────────────────────────────────────────────────────────────
model               gpt-4o-mini            config file
format              conventional           config file
history_depth       5                      default
timeout             30                     default
copy_to_clipboard   false                  default
...
```

### Set a configuration value

```bash
# Set your preferred model
gmuse config set model gpt-4o

# Set message format
gmuse config set format conventional

# Enable branch context
gmuse config set include_branch true

# Increase history depth
gmuse config set history_depth 15
```

### Verify your changes

```bash
gmuse config view
```

## Common Workflows

### First-time setup

```bash
# Configure your preferred model and format
gmuse config set model gpt-4o-mini
gmuse config set format conventional
gmuse config set history_depth 10

# Verify
gmuse config view
```

### Switch between formats

```bash
# Use conventional commits (feat:, fix:, etc.)
gmuse config set format conventional

# Use gitmoji (🎨, 🐛, etc.)
gmuse config set format gitmoji

# Use freeform (natural language)
gmuse config set format freeform
```

### Enable branch-aware commits

```bash
# Include branch name as context
gmuse config set include_branch true

# Optionally increase branch summary length
gmuse config set branch_max_length 80
```

### Adjust LLM parameters

```bash
# Lower temperature for more consistent output
gmuse config set temperature 0.3

# Increase token limit for longer messages
gmuse config set max_tokens 800

# Extend timeout for slow connections
gmuse config set timeout 60
```

## Error Handling

### Invalid key

```bash
$ gmuse config set unknown_key value
Error: Unknown configuration key: 'unknown_key'

Valid keys: branch_max_length, chars_per_token, copy_to_clipboard, format,
            history_depth, include_branch, learning_enabled, log_file,
            max_diff_bytes, max_message_length, max_tokens, model, provider,
            temperature, timeout
```

### Invalid value

```bash
$ gmuse config set history_depth 100
Error: history_depth must be between 0 and 50, got 100

Allowed range: 0-50
```

```bash
$ gmuse config set format invalid
Error: Invalid format: 'invalid'. Must be one of: freeform, conventional, gitmoji
```

## Config File Location

By default, configuration is stored at:

- **Linux/macOS**: `~/.config/gmuse/config.toml`
- **With XDG**: `$XDG_CONFIG_HOME/gmuse/config.toml`

The `gmuse config view` command always shows the file location.

## Available Configuration Keys

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `model` | string | null | LLM model name (e.g., `gpt-4o-mini`) |
| `provider` | string | null | LLM provider (`openai`, `anthropic`, `gemini`, etc.) |
| `format` | string | `freeform` | Message format (`freeform`, `conventional`, `gitmoji`) |
| `history_depth` | int | 5 | Recent commits for style context (0-50) |
| `timeout` | int | 30 | API timeout in seconds (5-300) |
| `temperature` | float | 0.7 | LLM sampling temperature (0.0-2.0) |
| `max_tokens` | int | 500 | Maximum tokens in response (1-100000) |
| `copy_to_clipboard` | bool | false | Auto-copy message to clipboard |
| `include_branch` | bool | false | Include branch name as context |
| `branch_max_length` | int | 60 | Max branch summary length (20-200) |
| `learning_enabled` | bool | false | Enable learning mode |
| `log_file` | string | null | Debug log file path |
| `max_diff_bytes` | int | 20000 | Max diff size before truncation |
| `max_message_length` | int | 1000 | Max commit message length |
| `chars_per_token` | int | 4 | Token estimation heuristic |

## Tips

1. **Environment variables take precedence**: If you have `GMUSE_FORMAT=gitmoji` set, it overrides the config file. Use `gmuse config view` to see which values are overridden.

2. **Reset to default**: Set a value to `null` to remove it from the config file:
   ```bash
   gmuse config set model null
   ```

3. **API keys stay in environment**: The `config set` command cannot store API keys. Continue using environment variables for `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.

## Next Steps

- Run `gmuse msg` to generate a commit message with your new settings
- Run `gmuse info` to see the resolved model and provider
- See [Configuration Reference](../../../docs/source/reference/configuration.md) for full details
