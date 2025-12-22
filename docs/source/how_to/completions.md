# Shell completions

This page describes how to install a *shell* completion script to get AI-powered
commit message suggestions when completing `git commit` messages. Currently,
`zsh` is supported; other shells may be added in the future.

## Quickstart

Quickly load the Zsh completion into your current shell and test it locally:

1. Load completions for the current session (temporary):

```console
# load completions into current shell (temporary)
$ eval "$(gmuse completions zsh)"
```

2. Ensure you have staged changes so gmuse has context:

```console
$ git add .  # stage your changes
```

3. Test the completion:

```console
$ git commit -m <TAB>
# gmuse will generate a suggested commit message and insert it into the -m argument
```

To persist the completion across sessions, add the `eval` line to your `~/.zshrc` and restart your shell (or run `exec zsh`).

## Supported shells

- `zsh` — supported (see installation below)
- Other shells — planned (contributions welcome)

## Installation

Generic installation (replace `<shell>` with the shell name):

```console
# add to your shell startup file
$ eval "$(gmuse completions <shell>)"
```

Zsh example (current): add the following to your `~/.zshrc`:

```console
$ eval "$(gmuse completions zsh)"
```

Then restart your shell or open a new session (e.g. `exec zsh` for Zsh).

## Usage

- Stage some changes: `git add .`
- Type `git commit -m ` and press TAB — gmuse will generate a suggestion and
  insert it into the `-m` argument.

Note: To avoid surprising behavior, the completion only runs when the message
argument is empty. If you've already typed a message after `-m`, pressing TAB
falls back to the shell's normal completion behavior.

## Configuration

Environment variables:

- `GMUSE_COMPLETIONS_ENABLED` (default `true`) — enable/disable completions
- `GMUSE_COMPLETIONS_TIMEOUT` (default `3.0`) — generation timeout in seconds
- `GMUSE_COMPLETIONS_CACHE_TTL` (default `30`) — completion-side cache TTL in seconds

## Developer & implementation notes

For implementation details, the runtime helper contract, and a checklist for
adding new shells, see the developer guide: `docs/source/development/shell-completions.md`.


## Troubleshooting & Notes

- If there are no staged changes, the completion will show a short warning and
  will not insert any text.
- The current Zsh implementation avoids adding `jq` as a dependency and
  instead uses small `sed` expressions to extract the minimal fields from the
  JSON response — other shells may choose different strategies.
- This is an opt-in, local feature — no new network requests are made unless
  the runtime helper calls the configured LLM provider.

For detailed developer notes for the Zsh implementation, see the project
specification: `specs/002-zsh-completions/spec.md`.
