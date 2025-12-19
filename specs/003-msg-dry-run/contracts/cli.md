# CLI Contract: `gmuse msg --dry-run`

## Command

- `gmuse msg --dry-run`

## Flags

- `--dry-run` (boolean)
  - Behavior: Do not call any LLM provider. Assemble prompts and print them.

All existing flags remain supported and should influence prompt assembly exactly as in non-dry-run runs:

- `--hint/-h`
- `--format/-f`
- `--model/-m`
- `--history-depth`
- `--provider`
- `--copy/-c`

## Output

Stdout MUST be plain text, in the exact order below.

### Output layout

```
MODEL: <model or none>
FORMAT: <format>
TRUNCATED: true|false

SYSTEM PROMPT:
<system_prompt>

USER PROMPT:
<user_prompt>
```

Notes:

- `<model or none>`: if a model resolves to an empty/None value, print `none`.
- `<format>`: the effective format resolved from config/CLI.
- `TRUNCATED` MUST reflect whether the staged diff was truncated.

## Errors and exit codes

- Dry-run MUST preserve the same behavior as `gmuse msg` when errors occur:
  - Not in a git repository → non-zero exit code and actionable message.
  - No staged changes → non-zero exit code and actionable message.

## Non-goals

- JSON output is not part of this MVP.
