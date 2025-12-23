# How it Works

This page explains the "invisible" logic behind `gmuse`—from how it extracts data from your repository to how it communicates with Large Language Models.

It is for users who want to understand what gmuse sends to an LLM, how prompts are assembled, and how generated messages are validated.

## The Execution Pipeline

When you run `gmuse msg`, the following sequence occurs:

1.  **Extraction**: `gmuse` queries your local Git repository to extract the currently staged diff and the last few commit messages for style reference. See **What is sent to the provider** below for details about what is included and provider handling.
2.  **Context Assembly**: It merges your diff with project-specific instructions from a `.gmuse` file (if present) and your optional `--hint`.
3.  **Prompting**: A two-part prompt (System + User) is constructed and sent to your chosen LLM provider via [LiteLLM](https://github.com/BerriAI/litellm), which provides a unified interface to many providers. Prompts are constructed locally and sent directly to the configured provider (gmuse does not proxy prompts through a gmuse-hosted server); see **What is sent to the provider** and [Privacy & Security](privacy.md) for provider retention details.
4.  **Validation**: The generated message is checked against the requested format and length constraints. If validation fails, `gmuse` will display a clear error and prevent the commit from proceeding; common error examples include:
    * "Generated message is empty"
    * "Message too long: 1200 characters (max 1000)"
    * "Message does not match Conventional Commits format"
   Validation rules include format-specific checks (Conventional, Gitmoji) and a maximum message length (1000 characters). Choose the expected format using `--format` or in your configuration.

## Output & clipboard behavior

By default `gmuse` prints the generated message to stdout; copying to the system clipboard is opt‑in. Pass `--copy` or set `copy_to_clipboard = true` in your configuration to enable copying. Clipboard operations use `pyperclip` from the optional `gmuse[clipboard]` extra; the CLI will warn if the dependency or a system clipboard utility (e.g., `pbcopy`, `xclip`, `wl-copy`) is missing. `--dry-run` never copies output; shell completions insert the suggestion into `git commit -m` rather than copying it to the clipboard.

## What is sent to the provider

When `gmuse` calls the LLM provider it sends the assembled prompts (System + User). The user prompt typically includes:

* Staged diff (raw diff; may be truncated to fit token limits)
* A short staged changes summary (files changed, lines added/removed)
* Recent commit messages for style reference (default 5, configurable via `--history-depth`)
* Repository instructions from a `.gmuse` file (if present)
* The CLI `--hint` value (if provided)
* Format/task instructions and any examples or templates

**Note:** gmuse does **not** send unstaged changes, your API keys, files outside the repository, or environment variables — see [](./privacy.md#what-is-never-sent) for full details on what is never sent and provider retention policies.

## Truncation Policy

Large diffs are automatically truncated to fit within token limits (default: **20,000 bytes ≈ 5,000 tokens**). This limit is **configurable** via `max_diff_bytes`:

```toml
# ~/.config/gmuse/config.toml
max_diff_bytes = 50000  # Allow larger diffs
```

Or via CLI flag:
```console
$ gmuse msg --max-diff-bytes 30000
```

> **Note:** Token estimation uses a simple heuristic of ~4 characters per token (also configurable via `chars_per_token`), which is approximate for GPT-style models. Actual token counts vary by model and tokenizer.

**How truncation works:**

1. File headers (`diff --git`, `---`, `+++`) are always preserved for context.
2. Content lines are kept until the byte limit is reached.
3. When truncated, a marker `... (diff truncated for brevity)` is appended.
4. The `TRUNCATED: true` flag appears in `--dry-run` output when truncation occurred.

If you see truncation warnings, consider:
- Splitting large changes into smaller, focused commits
- Increasing `max_diff_bytes` if your provider supports larger contexts
- Reviewing the full diff separately before committing

## Intelligence & Context

The "magic" of `gmuse` isn't just sending a diff to an AI; it's about providing the right **context** so the AI sounds like a contributor to *your* specific project.

### Style Matching (Few-Shot Learning)
By default, `gmuse` pulls the last 5 commit messages from your current branch and **explicitly includes them in the prompt** as style examples. The LLM is given these concrete examples so it can:
*   Identify preferred terminology.
*   Match the verbosity of existing messages.
*   Reproduce prefix or tagging conventions (like `PROJ-123:`) already in use.

> **Note:** The model doesn't magically "infer" your style—it's given your recent commits as explicit examples via `build_context()` in the prompt assembly.

### Repository Instructions
If a `.gmuse` file is found, its contents are injected directly into the prompt. This is perfect for team-wide rules like *"Always reference a Jira ticket"* or *"Keep descriptions under 50 characters."* See the [Configuration Guide](../how_to/configuration.md) for details.

## Prompting Strategy

We use a layered prompting approach to ensure consistent, high-quality output.

### 1. The System Persona
The LLM is initialized with a "System Prompt" that defines its identity as an expert developer. It is given strict guidelines:
*   Focus on **WHAT** changed and **WHY** (not just a list of files).
*   Use the **imperative mood** (e.g., "Add feature" instead of "Added feature").
*   Prioritize clarity over cleverness.

### 2. The Task Template
Depending on your chosen format, a specific task template is appended to the prompt:
*   **Conventional**: Defines the `type(scope): description` structure and provides allowed types (feat, fix, etc.).
*   **Gitmoji**: Provides a mapping of emojis to intents and ensures the emoji prefix is used.
*   **Freeform**: Instructs the model to use natural, concise language.

## Debugging & dry-run

> **Debugging & Troubleshooting:** For practical debugging steps (dry-run usage, provider diagnostics, sample outputs), see the [Troubleshooting guide](../how_to/troubleshooting.md).

## Generation Parameters

gmuse uses several configurable parameters to control how the LLM generates commit messages:

- **temperature** (default: 0.7): Controls randomness/creativity (0.0 = deterministic, 2.0 = very creative)
- **max_tokens** (default: 500): Maximum number of tokens in the generated response
- **max_diff_bytes** (default: 20000): Maximum diff size sent to the LLM
- **max_message_length** (default: 1000): Maximum commit message length (validation)
- **chars_per_token** (default: 4): Token estimation heuristic

All of these are configurable via CLI flags, environment variables, or config file. See the [Configuration Reference](../reference/configuration.md#llm-generation-parameters) for complete details and usage examples.

**Quick examples:**

```console
# More deterministic messages (CI/CD)
$ gmuse msg --temperature 0.0

# Shorter messages
$ gmuse msg --max-tokens 200

# Larger diff context
$ gmuse msg --max-diff-bytes 50000
```

For persistent settings, add them to your config file:
```toml
temperature = 0.3
max_tokens = 200
max_diff_bytes = 30000
```

## Validation Rules

For exact validation rules, canonical error messages, examples, and minimal failing/passing examples, see the [](../reference/validation.md).

## Error Handling

For common provider errors, sample messages, and recovery steps, see [](../how_to/troubleshooting.md#error-handling).

## Example: Tracing a Generation

To see how these layers come together, imagine you are fixing a security vulnerability.

### 1. The Ingredients
*   **Staged Diff**:
    ```diff
    - cursor.execute("SELECT * FROM users WHERE id = " + user_id)
    + cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    ```
*   **Style Reference**: `gmuse` scans your history and sees messages like
    ```text
    PROJ-123: Add login endpoint
    PROJ-456: Fix logout redirect
    ```
*   **User Hint**: You run `gmuse msg --hint "PROJ-789"`.
*   **Repository instructions**: A `.gmuse` file (e.g., `Always reference a Jira ticket`).
*   **Task template**: The format's task prompt (Conventional/Gitmoji/Freeform) — selected via `--format` or your config — is **automatically appended** to the user prompt by `gmuse` and enforces structure and constraints (for example, Conventional requires `type(scope): description` and a concise one-line message). You do not need to provide a separate template.

### 2. The Context Assembly
`gmuse` constructs a structured prompt using three distinct layers:

1.  **Instructions (System Prompt)**: The "Expert Developer" persona and guidelines (use imperative mood, focus on WHAT and WHY, etc.). See `SYSTEM_PROMPT` in `src/gmuse/prompts.py`.
2.  **Evidence (Context in User Prompt)**: The LLM is **explicitly given** your recent commits as style examples, your `--hint`, and any repository instructions. It doesn't infer patterns from nothing—it has concrete examples like `PROJ-123: Add login endpoint` to reproduce.
3.  **Task Template**: The format-specific instructions (Conventional/Gitmoji/Freeform) are appended to the user prompt. For Conventional, this includes the allowed types (`feat`, `fix`, etc.) and format rules.

This assembly happens in `build_prompt()` (see `src/gmuse/prompts.py`), which returns the `(system_prompt, user_prompt)` tuple sent to the LLM.

### 3. The Assembled Prompts

For this example, the assembled prompts would look like:

**System Prompt:**
```text
You are an expert commit message generator. Your role is to analyze code changes
and produce clear, informative commit messages...
```

**User Prompt:**
```text
Recent commits for style reference:
- PROJ-456: Fix logout redirect
- PROJ-123: Add login endpoint

Repository instructions:
Always reference a Jira ticket in the format PROJ-NNN.

User hint: PROJ-789

Staged changes summary:
- Files changed: 1
- Lines added: 1
- Lines removed: 1

Diff:
diff --git a/database.py b/database.py
...
- cursor.execute("SELECT * FROM users WHERE id = " + user_id)
+ cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))

Generate a commit message following Conventional Commits specification.
Format: type(scope): description
...
```

### 4. The LLM Response

The LLM combines the technical change (parameterized query), the style examples (`PROJ-NNN` prefix pattern), the repository instruction ("Always reference a Jira ticket"), and your hint (`PROJ-789`) to produce:

```text
fix(database): PROJ-789: use parameterized query to prevent SQL injection
```

### 5. Validation

Before returning the message, `gmuse` runs `validate_message()` (see `src/gmuse/prompts.py`):

- ✅ **Not empty**: Message has content
- ✅ **Length check**: 68 characters < 1000 max
- ✅ **Conventional format**: Matches `^(feat|fix|docs|...)\(.*\)?: .+`

Validation passes, and the message is displayed (or copied to clipboard if `--copy` was used).

## See Also

*   [Privacy & Security](privacy.md): Learn how we keep your code safe.
*   [Configuration](../how_to/configuration.md): Customize how `gmuse` behaves in your project.
