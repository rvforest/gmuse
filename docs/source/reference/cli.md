# CLI Reference

## gmuse msg

Generate a commit message from staged changes.

```console
$ gmuse msg [OPTIONS]
```

### Options

- `--hint TEXT` / `-h TEXT`: Provide a hint to the LLM (e.g., "security fix").
- `--format TEXT` / `-f TEXT`: Message format: `freeform` (default), `conventional`, or `gitmoji`.
- `--model TEXT` / `-m TEXT`: LLM model to use (overrides env/config).
- `--history-depth INTEGER`: Number of recent commits to use for style context (0–50).
- `--copy` / `-c`: Copy the generated message to clipboard.
- `--dry-run`: Print the assembled prompt without calling the LLM provider.

**Note:** Provider selection is auto-detected from configured API keys (e.g., `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`). Empty environment values fall through to the OS keyring, and `gmuse auth` provides the secure setup path for interactive use. See [Configuration Reference](configuration.md#model) for details on provider detection.

### Dry-run example

```console
$ gmuse msg --dry-run
```

Output:

```text
MODEL: gpt-4o-mini
FORMAT: freeform
TRUNCATED: false

SYSTEM PROMPT:
...

USER PROMPT:
...
```

Useful for debugging, auditing, or inspecting the prompt before calling the LLM.

## gmuse info

Display resolved configuration for debugging.

```console
$ gmuse info
```

## gmuse auth

Manage API credentials stored in the OS keyring.

```console
$ gmuse auth set OPENAI_API_KEY
$ gmuse auth set OPENAI_API_KEY --force
$ gmuse auth status
$ gmuse auth status openai
$ gmuse auth remove OPENAI_API_KEY
$ gmuse auth remove OPENAI_API_KEY ANTHROPIC_API_KEY
```

`gmuse auth set` prompts for a secret and stores it under the `gmuse` keyring service. `gmuse auth status` shows the managed keys and their masked values, and `gmuse auth remove` deletes one or more stored credentials.

Status `Source` values mean:

- `env`: resolved from an environment variable
- `keyring`: resolved from the OS keyring
- `missing`: no credential found
- `timeout`: keyring lookup exceeded the completion safety budget

## gmuse git-completions

Generate shell completion scripts.

```console
$ gmuse git-completions zsh
```
