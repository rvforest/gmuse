# Zsh completions (gmuse)

This page describes how to install the Zsh completion script to get AI-powered
commit message suggestions when completing git commit messages.

## Installation

1. Add the following to your `~/.zshrc`:

```zsh
eval "$(gmuse completions zsh)"
```

2. Restart Zsh:

```zsh
exec zsh
```

## Usage

- Stage some changes: `git add .`
- Type `git commit -m ` and press TAB — gmuse will generate a suggestion and
  insert it into the `-m` argument.
- Provide a hint: `git commit -m "fix auth` + TAB — the current word will be
  passed as a hint to help guide the generated message.

## Configuration

Environment variables:

- `GMUSE_COMPLETIONS_ENABLED` (default `true`) — enable/disable completions
- `GMUSE_COMPLETIONS_TIMEOUT` (default `3.0`) — generation timeout in seconds
- `GMUSE_COMPLETIONS_CACHE_TTL` (default `30`) — zsh-side cache TTL in seconds

## Runtime helper contract

The completion script calls the runtime helper `gmuse completions-run` with
arguments `--shell zsh --for "git commit -m" --hint <hint>` and expects a JSON
response of the form:

```json
{
  "suggestion": "feat: add login",
  "status": "ok",
  "metadata": {
    "truncated": false,
    "elapsed_ms": 1200
  }
}
```

Status values: `ok`, `timeout`, `offline`, `no_staged_changes`, `error`.

## Troubleshooting & Notes

- If there are no staged changes, the completion will show a short warning
  (using `_message`) and will not insert any text.
- The Zsh script avoids adding `jq` as a dependency and instead uses small
  `sed` expressions to extract the minimal fields from the JSON response.
- This is an opt-in, local feature — no new network requests are made unless
  the runtime helper calls the configured LLM provider.

For detailed developer notes and contract information, see the project
specification: `specs/002-zsh-completions/spec.md`.
