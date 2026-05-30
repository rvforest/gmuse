# CLI Reference

## gmuse msg

Generate a commit message from staged changes.

```console
$ gmuse msg [OPTIONS]
```

### Options

- `--hint TEXT` / `-h TEXT`: Provide a hint to the LLM (e.g., "security fix").
- `--format TEXT` / `-f TEXT`: Message format: `freeform` (default), `conventional`, or `gitmoji`.
- `--backend TEXT`: LLM backend to use (for example, `openai`, `anthropic`, `cohere`).
- `--model TEXT` / `-m TEXT`: LLM model to use (overrides env/config).
- `--history-depth INTEGER`: Number of recent commits to use for style context (0–50).
- `--copy` / `-c`: Copy the generated message to clipboard.
- `--dry-run`: Print the assembled prompt without calling the selected LLM backend.

**Note:** Backend resolution follows `CLI > environment > config file > automatic fallback`. Automatic fallback first honors a model's native backend hint, then uses a single configured compatible backend, and otherwise fails with an actionable ambiguity error. See [Configuration Reference](configuration.md#backend) for details.

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

`gmuse info` reports the resolved backend, resolved model, and resolution source, followed by the relevant credential-related environment variables.

## gmuse git-completions

Generate shell completion scripts.

```console
$ gmuse git-completions zsh
```
