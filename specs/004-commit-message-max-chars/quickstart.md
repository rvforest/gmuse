````markdown
# Quickstart: Commit Message Max Characters (`max_chars`)

This feature adds an optional `max_chars` configuration setting that constrains generated commit message length and includes the limit in the prompt.

## Configure via config file

Edit your config at the XDG path (default):

- `~/.config/gmuse/config.toml`

Add:

```toml
max_chars = 120
```

## Configure via environment variable

```bash
export GMUSE_MAX_CHARS=120
```

## Run

```bash
gmuse msg
```

## Expected behavior

- If `max_chars` is set:
  - The prompt explicitly includes the maximum character constraint.
  - If the model output exceeds the limit, `gmuse` exits non-zero with an actionable error including actual length and limit.
- If `max_chars` is not set:
  - Behavior remains unchanged.

````
