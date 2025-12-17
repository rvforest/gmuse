# Shell completions — Developer guide (gmuse)

This document is intended for implementors who want to add or maintain shell
completion support in gmuse. The canonical, detailed implementation notes for
Zsh are kept in `specs/002-zsh-completions/spec.md` — use that spec as the
single source of truth for any compatibility or protocol requirements.

## Runtime helper contract

Completion scripts should invoke the runtime helper `gmuse completions-run`
with arguments `--shell <shell> --for "git commit -m"` and expect a JSON
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

Completion scripts must:

- Parse `suggestion` and insert it into the appropriate argument or buffer
  location for the target shell.
- Inspect `status` and implement reasonable fallbacks (e.g., show a short
  warning when `no_staged_changes` is returned).
- Treat the `metadata` fields as auxiliary for observability and logging.

## Implementation checklist

- Implement a completion script for the target shell that:
  - Calls `gmuse completions-run --shell <shell> --for "git commit -m"`
  - Parses the returned JSON and extracts `suggestion` and `status`
  - Inserts the suggestion only when appropriate (e.g., when the message
    argument is empty)
  - Falls back to the shell's normal completion behavior when needed
- Add or update automated tests where possible (unit tests for parsing,
  integration tests that exercise `gmuse completions-run` and the completion
  script in a controlled environment).
- Document installation and usage in `docs/source/getting_started/completions.md`
  by adding the shell to the **Supported shells** section and linking to this
  developer guide for implementors.
- If the new shell requires special contract extensions or behaviors, add
  or extend a spec under `specs/` and reference it from this guide.

## Zsh notes & testing

- The current Zsh implementation keeps the completion script dependency-free
  and uses small `sed` expressions instead of `jq` to extract the minimal
  JSON fields. Other shells may choose different strategies.
- For local testing of the runtime helper, run:

```sh
GMUSE_DEBUG=1 gmuse completions-run --shell zsh --for "git commit -m" --hint "start of message" --timeout 3.0
```

(adjust `--shell` and other args as needed for the target shell).

## Contributing & specs

- For Zsh-specific low-level details, see: `specs/002-zsh-completions/spec.md`.
- Prefer updating the spec for any contract changes and link the spec from
  this guide to avoid duplication.
- When opening a PR, include tests and a short usage example in `docs/` for
  the new shell.
