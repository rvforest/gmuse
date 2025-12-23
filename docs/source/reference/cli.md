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

**Note:** Provider selection is auto-detected from configured API keys (e.g., `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`). To override, set the `GMUSE_PROVIDER` environment variable or add `provider = "<provider>"` to your config file.
- `--copy` / `-c`: Copy the generated message to clipboard.
- `--dry-run`: Print the assembled prompt without calling the LLM provider.

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

## gmuse git-completions

Generate shell completion scripts.

```console
$ gmuse git-completions zsh
```
