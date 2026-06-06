# CLI Contract: commit / generate / msg

**Feature**: 008-commit-ux-redesign
**Date**: 2026-06-06

## Top-level help contract

`gmuse --help` must present `commit` as the primary workflow and `generate` as the raw primitive.

```text
Usage: gmuse [OPTIONS] COMMAND [ARGS]...

  gmuse: AI generated commit messages.

  Primary workflow:
    gmuse commit      Generate a draft and create a git commit

  Raw generation:
    gmuse generate    Print a generated commit message to stdout

  Compatibility:
    gmuse msg         Deprecated alias for 'gmuse generate'

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.
```

`git-completions`, `git-completions-run`, `config`, `auth`, and `info` remain available.

---

## Command: `gmuse commit`

### Signature

```text
gmuse commit [OPTIONS]
```

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--hint` | str | `None` | Additional generation guidance |
| `--model`, `-m` | str | `None` | LLM model override |
| `--format`, `-f` | str | resolved config | Commit message format |
| `--history-depth` | int | resolved config | Number of recent commits for style context |
| `--temperature` | float | resolved config | Sampling override |
| `--max-tokens` | int | resolved config | Response token cap |
| `--max-diff-bytes` | int | resolved config | Diff truncation threshold |
| `--include-branch` | bool | false | Include sanitized branch context |
| `--yes`, `-y` | bool | false | Skip review and commit the first generated draft immediately |
| `--help` | bool | false | Show help and exit |

### Behavior contract

1. Reuse the same raw generation inputs and validation rules as `gmuse generate`.
2. If `--yes` is set:
   - generate one draft;
   - run a direct `git commit`;
   - do not prompt or launch an editor.
3. If `--yes` is not set and stdin/stdout are interactive:
   - generate one draft;
   - display the draft for review;
   - present `accept`, `edit`, `regenerate`, and `abort` actions.
4. `accept` creates a commit from the current draft without another LLM call.
5. `edit` launches the user's normal git editor flow with the draft prefilled.
6. `regenerate` requests a fresh draft and returns to the same review step.
7. `abort` exits without creating a commit.
8. If stdin/stdout are not interactive and `--yes` is not set, fail fast with actionable guidance.
9. `gmuse commit` must not expose `--copy`.
10. Legacy clipboard config/env inputs must not cause commit-time copy side effects.

### Success output

**Interactive accept**:

```text
Draft commit message:

feat: add branch-aware commit flow

Choose an action: [a]ccept, [e]dit, [r]egenerate, [x]abort
```

On commit success, the command may print a concise success confirmation or stream git's normal success output, but it must not claim success before git returns exit code `0`.

### Non-interactive guard

**Error (exit code 1)**:

```text
Error: gmuse commit requires an interactive terminal unless --yes is provided.

Use 'gmuse commit --yes' to commit immediately, or 'gmuse generate' for stdout-only output.
```

### Git/editor failure shape

**Error (exit code 1)**:

```text
Error: Git could not create the commit.

<git stderr or actionable summary>
```

If the editor path exits without creating a commit, the command must report that no commit was created and must not print a success-shaped message.

---

## Command: `gmuse generate`

### Signature

```text
gmuse generate [OPTIONS]
```

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--hint` | str | `None` | Additional generation guidance |
| `--model`, `-m` | str | `None` | LLM model override |
| `--format`, `-f` | str | resolved config | Commit message format |
| `--history-depth` | int | resolved config | Number of recent commits for style context |
| `--temperature` | float | resolved config | Sampling override |
| `--max-tokens` | int | resolved config | Response token cap |
| `--max-diff-bytes` | int | resolved config | Diff truncation threshold |
| `--include-branch` | bool | false | Include sanitized branch context |
| `--dry-run` | bool | false | Print the assembled prompt instead of calling the provider |
| `--help` | bool | false | Show help and exit |

### Behavior contract

1. Gather context through the existing shared generation path.
2. On success, print only the generated message to stdout.
3. Preserve truncation warnings on stderr when diff context is reduced.
4. Preserve existing prerequisite failures for not-a-repo, no staged changes, missing credentials, and invalid generated output.
5. Never prompt, open an editor, create a git commit, or perform clipboard actions.
6. Do not expose `--copy`.
7. Ignore passive legacy clipboard config/env inputs so raw success stays stdout-only.

### Success output

```text
feat: add branch-aware commit flow
```

### Dry-run output

`--dry-run` continues to print prompt-inspection output instead of a generated message and does not call the LLM provider.

---

## Command: `gmuse msg`

### Signature

```text
gmuse msg [OPTIONS]
```

### Compatibility policy

- `gmuse msg` is a temporary deprecated alias for `gmuse generate`.
- During the transition line it must preserve raw stdout compatibility for existing scripts.
- Deprecation guidance must be written to stderr, not stdout.

### Behavior contract

1. Accept the same raw-generation options as `gmuse generate`, except for retired clipboard behavior.
2. Emit a deprecation notice naming:
   - `gmuse generate` for raw-output workflows
   - `gmuse commit` for direct commit workflows
3. Delegate to the same shared raw-generation helper as `gmuse generate`.
4. Keep stdout identical to `gmuse generate` on success.

### Deprecation notice

```text
Warning: 'gmuse msg' is deprecated and will be removed after the transition period.

Use 'gmuse generate' for stdout-only commit message generation.
Use 'gmuse commit' to generate a draft and create the git commit directly.
```

### Legacy clipboard failure

If a user runs `gmuse msg --copy`, the command must fail and must not generate a commit message.

**Error (exit code 1)**:

```text
Error: Clipboard-first behavior has been retired.

Use 'gmuse commit' to create the commit directly, or pipe 'gmuse generate' into your own clipboard tool.
```

---

## Legacy clipboard inputs

### Removed CLI flag

- `--copy` must not appear in `gmuse commit --help` or `gmuse generate --help`.
- `gmuse msg --copy` is retained only as a migration error trigger.

### Legacy environment/config compatibility

| Legacy input | New contract |
|--------------|--------------|
| `GMUSE_COPY` | Deprecated; parsed only for compatibility, but must not trigger copy behavior on `generate`, `commit`, or completion runtime |
| `copy_to_clipboard` | Deprecated; same compatibility rule as `GMUSE_COPY` |

These inputs may produce migration warnings in user-facing command paths, but they must never contaminate `gmuse generate` stdout.

## Exit codes

| Exit Code | Meaning |
|-----------|---------|
| `0` | Success |
| `1` | User-facing CLI/git/migration/prerequisite error |
| `2` | Provider or generated-message validation failure on raw generation paths |
