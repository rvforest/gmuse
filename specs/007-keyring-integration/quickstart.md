# Quickstart: Secure API Key Management

This feature adds secure OS keyring support to `gmuse` while keeping environment variables as the preferred path for non-interactive environments.

## 1. Store a key for interactive use

```bash
gmuse auth set OPENAI_API_KEY
```

Expected behavior:

- `gmuse` checks that a secure keyring backend is available before prompting.
- The prompt hides the key as you type.
- The secret is stored in the OS keyring under the `gmuse` namespace.

## 2. Inspect stored credentials

```bash
gmuse auth status
```

Expected behavior:

- Output lists only gmuse-managed variables from the hidden index entry.
- Values are masked.
- Each row shows whether the active value comes from the environment or keyring.

To inspect a provider's full requirement set:

```bash
gmuse auth status openai
```

That path uses LiteLLM provider validation rules to report whether required variables are available.

## 3. Use `gmuse msg` without exporting a key every session

```bash
unset OPENAI_API_KEY
gmuse msg
```

Expected behavior:

- If no non-empty env var is set, `gmuse` falls back to the secure keyring entry.
- If nothing is configured anywhere, `gmuse` exits with guidance for both interactive setup and CI usage.

## 4. Remove stored credentials

```bash
gmuse auth remove OPENAI_API_KEY ANTHROPIC_API_KEY
```

Expected behavior:

- Matching keyring entries are deleted.
- The hidden managed-key index is updated.
- Missing variables are reported gracefully rather than crashing.

## 5. Linux or WSL fallback

```bash
gmuse auth set OPENAI_API_KEY
```

If no secure keyring backend is available, `gmuse` must fail before prompting and direct you to use environment variables instead:

```bash
export OPENAI_API_KEY="sk-..."
gmuse msg
```

## 6. Completion behavior stays non-blocking

```bash
gmuse git-completions-run --shell zsh --for "git commit -m"
```

Expected behavior:

- Completion-time credential access uses a strict 200ms timeout.
- If the keyring would block, prompt, or fail, completions exit cleanly with no suggestion rather than hanging the shell.
