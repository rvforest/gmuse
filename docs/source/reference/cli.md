# CLI Reference

## gmuse commit

Generate a commit message from staged changes and use it to create a git commit.

```console
$ gmuse commit [OPTIONS]
```

By default, `gmuse commit` runs an interactive review flow. It shows the generated
draft and lets you accept, edit, regenerate, or quit before a commit is created.

### Options

- `--hint TEXT` / `-h TEXT`: Provide a hint to the LLM (e.g., "security fix").
- `--edit`: Generate a draft, open the editor immediately with that draft prefilled, and commit after the editor exits.
- `--yes` / `-y`: Generate and commit immediately without prompting. Cannot be combined with `--edit`.
- `--format TEXT` / `-f TEXT`: Message format: `freeform` (default), `conventional`, or `gitmoji`.
- `--model TEXT` / `-m TEXT`: LLM model to use (overrides env/config).
- `--history-depth INTEGER`: Number of recent commits to use for style context (0–50).

## gmuse generate

Generate a commit message from staged changes and write only the message to stdout.

```console
$ gmuse generate [OPTIONS]
```

Use this command for scripts, shell integrations, and completion plumbing.

### Options

- `--hint TEXT` / `-h TEXT`: Provide a hint to the LLM (e.g., "security fix").
- `--format TEXT` / `-f TEXT`: Message format: `freeform` (default), `conventional`, or `gitmoji`.
- `--model TEXT` / `-m TEXT`: LLM model to use (overrides env/config).
- `--history-depth INTEGER`: Number of recent commits to use for style context (0–50).
- `--dry-run`: Print the assembled prompt without calling the LLM provider.

## gmuse msg

Deprecated compatibility alias for `gmuse generate`.

```console
$ gmuse msg [OPTIONS]
```

`gmuse msg` emits a deprecation notice on stderr and preserves the stdout-only
message output contract. Legacy clipboard mode is retired; `gmuse msg --copy`
fails with migration guidance.

**Note:** Provider selection is auto-detected from configured API keys (e.g., `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`). Empty environment values fall through to the OS keyring, and `gmuse auth` provides the secure setup path for interactive use. See [Configuration Reference](configuration.md#model) for details on provider detection.

### Dry-run example

```console
$ gmuse generate --dry-run
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
