# CLI Contracts: Global Config Commands

**Feature**: 004-global-config
**Date**: 2025-12-23

## Command Group: `gmuse config`

Parent command group for configuration management.

```
gmuse config [COMMAND]
```

### Help Text

```
Usage: gmuse config [OPTIONS] COMMAND [ARGS]...

  Manage gmuse global configuration.

  View and modify settings stored in ~/.config/gmuse/config.toml.
  These settings apply across all repositories unless overridden
  by environment variables or CLI flags.

Options:
  --help  Show this message and exit.

Commands:
  view  Display current global configuration.
  set   Set a global configuration value.
```

---

## Command: `gmuse config view`

Display the current global configuration.

### Signature

```
gmuse config view [OPTIONS]
```

### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--help` | | bool | false | Show help and exit |

### Output Contract

**Success (exit code 0)**:

```
Global config file: /home/user/.config/gmuse/config.toml

--- File Contents ---
model = "gpt-4o-mini"
format = "conventional"
history_depth = 10

--- Effective Configuration ---
Key                 Value                  Source
────────────────────────────────────────────────────────────
model               gpt-4o-mini            config file
format              conventional           config file
history_depth       10                     config file
timeout             30                     default
temperature         0.7                    default
max_tokens          500                    default
copy_to_clipboard   false                  default
include_branch      true                   env (GMUSE_INCLUDE_BRANCH) ⚠ overrides file
learning_enabled    false                  default
```

**No config file (exit code 0)**:

```
Global config file: /home/user/.config/gmuse/config.toml

No global configuration file found.
Create one with: gmuse config set <key> <value>

--- Effective Configuration ---
Key                 Value                  Source
────────────────────────────────────────────────────────────
model               None                   default
format              freeform               default
history_depth       5                      default
...
```

**Read error (exit code 1)**:

```
Error: Cannot read config file /home/user/.config/gmuse/config.toml: Permission denied

Check file permissions and try again.
```

**Invalid TOML (exit code 1)**:

```
Error: Invalid TOML syntax in /home/user/.config/gmuse/config.toml: Unexpected character at line 3

Fix the syntax error or delete the file to start fresh.
```

### Behavior Contract

1. Resolve config path via `get_config_path()`
2. If file exists:
   - Read and display raw file contents
   - Parse TOML (exit 1 on parse error)
3. If file does not exist:
   - Display "No global configuration file found" message
4. Merge config from: DEFAULTS ← ENV ← FILE
5. Display effective config table with source column
6. Mark keys where ENV overrides FILE with warning indicator

---

## Command: `gmuse config set`

Set a global configuration value.

### Signature

```
gmuse config set KEY VALUE [OPTIONS]
```

### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `KEY` | str | Yes | Configuration key to set |
| `VALUE` | str | Yes | Value to assign |

### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--help` | | bool | false | Show help and exit |

### Output Contract

**Success (exit code 0)**:

```
Set 'format' to 'conventional' in /home/user/.config/gmuse/config.toml
```

**Unknown key (exit code 1)**:

```
Error: Unknown configuration key: 'unknown_key'

Valid keys: branch_max_length, chars_per_token, copy_to_clipboard, format,
            history_depth, include_branch, learning_enabled, log_file,
            max_diff_bytes, max_message_length, max_tokens, model, provider,
            temperature, timeout
```

**Invalid value - type error (exit code 1)**:

```
Error: Cannot parse 'abc' as integer for 'history_depth'

Example: gmuse config set history_depth 10
```

**Invalid value - range error (exit code 1)**:

```
Error: history_depth must be between 0 and 50, got 100

Allowed range: 0-50
```

**Invalid value - choice error (exit code 1)**:

```
Error: Invalid format: 'invalid'. Must be one of: freeform, conventional, gitmoji
```

**Write error (exit code 1)**:

```
Error: Cannot write config file /home/user/.config/gmuse/config.toml: Permission denied

Check directory permissions and try again.
```

### Behavior Contract

1. Validate KEY exists in `ALLOWED_CONFIG_KEYS`
2. Infer expected type from `DEFAULTS[KEY]`
3. Parse VALUE to expected type
4. Validate parsed value (ranges, choices)
5. If config file exists:
   - Load with tomlkit (preserves comments)
   - Update/add key
6. If config file does not exist:
   - Create new tomlkit document
   - Add key
7. Create parent directories if needed
8. Write atomically (temp file + rename)
9. Print success message

---

## Error Codes

| Exit Code | Meaning |
|-----------|---------|
| 0 | Success |
| 1 | User error (invalid key, invalid value, file access) |
| 2 | Internal error (unexpected exception) |

---

## Examples

### View configuration

```bash
# View current settings
gmuse config view

# Pipe to grep for specific key
gmuse config view | grep history_depth
```

### Set configuration values

```bash
# Set model
gmuse config set model gpt-4o

# Set format
gmuse config set format conventional

# Set boolean (multiple accepted forms)
gmuse config set copy_to_clipboard true
gmuse config set include_branch yes
gmuse config set learning_enabled 1

# Set numeric values
gmuse config set history_depth 15
gmuse config set timeout 60
gmuse config set temperature 0.3

# Set optional string to null
gmuse config set model null
```

### Common workflows

```bash
# Quick setup
gmuse config set model gpt-4o-mini
gmuse config set format conventional
gmuse config view

# Reset to default by setting null
gmuse config set model null

# Debug: see what's overriding file settings
GMUSE_FORMAT=gitmoji gmuse config view
# Shows: format = conventional (env ⚠ overrides file)
```

---

## Python API Contract

### New Functions in `config.py`

```python
ALLOWED_CONFIG_KEYS: Final[frozenset[str]]
"""Set of valid configuration key names, derived from DEFAULTS."""

def parse_config_value(key: str, raw_value: str) -> Any:
    """Parse a string value to the appropriate type for a config key.

    Args:
        key: Configuration key name (must be in ALLOWED_CONFIG_KEYS)
        raw_value: User-provided string value

    Returns:
        Parsed value of appropriate type

    Raises:
        ConfigError: If key is unknown or value cannot be parsed
    """

def save_config(config_path: Path, updates: dict[str, Any]) -> None:
    """Save configuration updates to file, preserving existing content.

    Args:
        config_path: Path to config file
        updates: Dictionary of key-value pairs to set

    Raises:
        ConfigError: If file cannot be written
    """

def load_config_raw(config_path: Optional[Path] = None) -> str:
    """Load raw config file contents as string.

    Args:
        config_path: Path to config file, defaults to XDG location

    Returns:
        File contents as string, or empty string if file doesn't exist

    Raises:
        ConfigError: If file exists but cannot be read
    """

def get_effective_config_with_sources() -> list[EffectiveConfigEntry]:
    """Get merged configuration with source tracking.

    Returns:
        List of (key, value, source, override_warning) tuples
    """
```

### New CLI Module `cli/config.py`

```python
config_app = typer.Typer(help="Manage gmuse global configuration.")

@config_app.command()
def view() -> None:
    """Display current global configuration."""

@config_app.command()
def set(
    key: str = typer.Argument(..., help="Configuration key to set"),
    value: str = typer.Argument(..., help="Value to assign"),
) -> None:
    """Set a global configuration value."""
```

### Registration in `cli/main.py`

```python
from gmuse.cli.config import config_app

# In main.py, add to app
app.add_typer(config_app, name="config")
```
