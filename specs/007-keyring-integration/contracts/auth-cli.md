# CLI Contract: Authentication Commands

**Feature**: 007-keyring-integration
**Date**: 2026-06-02

## Command Group: `gmuse auth`

Parent command group for secure credential management.

```text
gmuse auth [COMMAND]
```

### Help Text

```text
Usage: gmuse auth [OPTIONS] COMMAND [ARGS]...

  Manage API credentials for gmuse.

  Store interactive credentials in the OS keyring. Environment variables remain
  the recommended path for non-interactive environments and always take precedence when set.

Options:
  --help  Show this message and exit.

Commands:
  remove  Remove one or more stored credentials.
  set     Store or replace a credential in the OS keyring.
  status  Show credential availability and storage source.
```

---

## Command: `gmuse auth set`

### Signature

```text
gmuse auth set VAR_NAME [--force]
```

### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `VAR_NAME` | str | Yes | Environment variable name to store, e.g. `OPENAI_API_KEY` |

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--force` | bool | false | Replace an existing key without interactive confirmation |
| `--help` | bool | false | Show help and exit |

### Behavior Contract

1. Validate that only `VAR_NAME` is passed; positional secret values are rejected.
2. Validate the active keyring backend before prompting.
3. If the backend is missing or insecure, exit non-zero with actionable guidance and do not prompt.
4. If an entry already exists and `--force` is not set:
   - Prompt `[y/N]` in interactive terminals.
   - Abort with an error in non-interactive terminals.
5. Prompt for the secret using masked input.
6. Store the secret under service `gmuse`, username `VAR_NAME`.
7. Add `VAR_NAME` to the `__gmuse_index__` entry.
8. Print a success message without revealing the secret.

### Output Contract

**Success (exit code 0)**:

```text
Stored OPENAI_API_KEY in the system keyring for gmuse.
```

**Missing secure backend (exit code 1)**:

```text
Error: No secure system keyring is available.

Use environment variables instead for this environment:
  export OPENAI_API_KEY='sk-...'
```

**Insecure backend rejected (exit code 1)**:

```text
Error: Active keyring backend is insecure and cannot be used.

gmuse refuses plaintext or null keyring backends. Use environment variables instead.
```

**Overwrite requires confirmation (exit code 1)**:

```text
Error: Credential for OPENAI_API_KEY already exists.

Re-run with --force or confirm overwrite in an interactive terminal.
```

---

## Command: `gmuse auth status`

### Signature

```text
gmuse auth status [PROVIDER]
```

### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `PROVIDER` | str | No | Optional LiteLLM provider name, e.g. `openai` |

### Behavior Contract

1. With no provider argument, read the `__gmuse_index__` entry and report only gmuse-managed variables.
2. For each variable, show whether the effective value comes from env or keyring and display only the masked value.
3. With a provider argument, use `litellm.validate_environment(model="<provider>/dummy")` to determine required variables, then resolve each via env/keyring.
4. Do not scan unrelated OS keychain items or dump the broader process environment.

### Output Contract

**Success (exit code 0)**:

```text
Credential status for gmuse

Variable          Source    Value
----------------  --------  ----------------
OPENAI_API_KEY    keyring   ************ABCD
```

**Provider status (exit code 0)**:

```text
Credential status for provider: openai

Variable          Source    Value
----------------  --------  ----------------
OPENAI_API_KEY    env       ************ABCD
```

**Unknown provider or validation error (exit code 1)**:

```text
Error: Could not validate credentials for provider 'unknown-provider'.
```

---

## Command: `gmuse auth remove`

### Signature

```text
gmuse auth remove VAR_NAME [VAR_NAME ...]
```

### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `VAR_NAME` | str | Yes | One or more environment variable names to delete |

### Behavior Contract

1. Accept one or more variable names.
2. Delete each matching keyring entry from service `gmuse`.
3. Remove deleted entries from the `__gmuse_index__` record.
4. Report missing entries gracefully rather than failing the whole command.

### Output Contract

**Success with removals (exit code 0)**:

```text
Removed 2 credential(s) from the system keyring.
```

**No matching entry (exit code 0)**:

```text
No stored credential found for INVALID_KEY.
```

## Exit Codes

| Exit Code | Meaning |
|-----------|---------|
| 0 | Success |
| 1 | User-facing auth/config/backend error |
| 2 | Unexpected internal error |
