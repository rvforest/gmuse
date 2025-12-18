# Contract: Runtime Helper

**Command**: `gmuse completions-run`

## Input (CLI Arguments)

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `--shell` | `str` | Yes | The target shell (e.g., `zsh`). |
| `--for` | `str` | Yes | The command being completed (e.g., `git commit -m`). |
| `--timeout` | `float` | No | Timeout in seconds (default: env var or 3.0). |

## Output (stdout)

JSON object with the following structure:

```json
{
  "suggestion": "feat: add login functionality",
  "status": "ok",
  "metadata": {
    "truncated": false,
    "elapsed_ms": 1200
  }
}
```

### Status Codes

- `ok`: Suggestion generated successfully.
- `timeout`: Generation timed out.
- `offline`: Network unavailable or credentials missing.
- `no_staged_changes`: No staged changes found.
- `error`: Internal error.

## Error Handling

- All errors (including exceptions) MUST be caught and returned as a JSON response with `status: "error"`.
- stderr MAY contain debug logs if `GMUSE_DEBUG` is set, but stdout MUST ONLY contain the JSON response.
