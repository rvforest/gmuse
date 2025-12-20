# How it Works

This page explains the "invisible" logic behind `gmuse`—from how it extracts data from your repository to how it communicates with Large Language Models.

It is for users who want to understand what gmuse sends to an LLM, how prompts are assembled, and how generated messages are validated.

## The Execution Pipeline

When you run `gmuse msg`, the following sequence occurs:

1.  **Extraction**: `gmuse` queries your local Git repository to extract the currently staged diff and the last few commit messages for style reference. See **What is sent to the provider** below for details about what is included and provider handling.
2.  **Context Assembly**: It merges your diff with project-specific instructions (from `.gmuse` or `pyproject.toml`) and your optional `--hint`.
3.  **Prompting**: A two-part prompt (System + User) is constructed and sent to your chosen LLM provider via [LiteLLM](https://github.com/BerriAI/litellm), which provides a unified interface to many providers (see [LLM Providers](llm_providers.md) for provider-specific details). Prompts are constructed locally and sent directly to the configured provider (gmuse does not proxy prompts through a gmuse-hosted server); see **What is sent to the provider** and [Privacy & Security](privacy.md) for provider retention details.
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
* Repository instructions from `.gmuse` or `[tool.gmuse.instructions]` in `pyproject.toml` (if present)
* The CLI `--hint` value (if provided)
* Format/task instructions and any examples or templates

**Note:** gmuse does **not** send unstaged changes, your API keys, files outside the repository, or environment variables — see [Privacy & Security → What is NEVER sent](privacy.md#what-is-never-sent) for full details on what is never sent and provider retention policies.

## Truncation Policy

Large diffs are automatically truncated to fit within token limits (default: **20,000 bytes ≈ 5,000 tokens**).

> **Note:** Token estimation uses a simple heuristic of ~4 characters per token, which is approximate for GPT-style models. Actual token counts vary by model and tokenizer.

**How truncation works:**

1. File headers (`diff --git`, `---`, `+++`) are always preserved for context.
2. Content lines are kept until the byte limit is reached.
3. When truncated, a marker `... (diff truncated for brevity)` is appended.
4. The `TRUNCATED: true` flag appears in `--dry-run` output when truncation occurred.

If you see truncation warnings, consider splitting large changes into smaller, focused commits.

## Intelligence & Context

The "magic" of `gmuse` isn't just sending a diff to an AI; it's about providing the right **context** so the AI sounds like a contributor to *your* specific project.

### Style Matching (Few-Shot Learning)
By default, `gmuse` pulls the last 5 commit messages from your current branch and **explicitly includes them in the prompt** as style examples. The LLM is given these concrete examples so it can:
*   Identify preferred terminology.
*   Provide a vocabulary for scopes and domain terms (e.g., `db`, `api`, `cli`) so generated messages use meaningful scopes.
*   Match the verbosity of existing messages.
*   Reproduce prefix or tagging conventions (like `PROJ-123:`) already in use.

> **Note:** The model doesn't magically "infer" your style—it's given your recent commits as explicit examples via `build_context()` in the prompt assembly, and those commits supply scope vocabulary and domain wording the model should follow.

### Repository Instructions
If a `.gmuse` file (or a `[tool.gmuse.instructions]` block in `pyproject.toml`) is found, its contents are injected directly into the prompt. This is perfect for team-wide rules like *"Always reference a Jira ticket"* or *"Keep descriptions under 50 characters."* See the [Configuration Guide](../how_to/configuration.md) for details.

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

For default generation settings and guidance on configuring them, see the [Configuration guide](../how_to/configuration.md#generation-parameters).

## Validation Rules

For exact validation rules, canonical error messages, examples, and minimal failing/passing examples, see the [Validation reference](../reference/validation.md#validation-rules).

## Error Handling

For common provider errors, sample messages, and recovery steps, see the [Troubleshooting guide — Error handling](../how_to/troubleshooting.md#error-handling).

## Example: Tracing a Generation

To see how these layers come together, imagine you are adding a database column and the accompanying migration.

### 1. The Ingredients
*   **Staged Diff**:
    ```diff
    diff --git a/migrations/0002_add_user_email.sql b/migrations/0002_add_user_email.sql
    new file mode 100644
    +CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, user_email VARCHAR(255));
    +ALTER TABLE users ADD COLUMN user_email VARCHAR(255);
    diff --git a/models/user.py b/models/user.py
    @@
     class User(Base):
    -    pass
    +    email = Column(String, nullable=True)
    ```
*   **Style Reference**

    `gmuse` scans your history and sees messages like:
    ```text
    feat(db): add connection pooling
    fix(api): handle invalid auth token
    chore(release): prepare v1.3.2 release
    perf(cache): reduce session serialization overhead
    fix(auth): validate token expiry in middleware
    ```
*   **User Hint** (optional)

    `--hint "add user email"` can be provided. This ensures the required migration details are available to the model even if it does not infer them from the diff. For migration-specific instructions you can include an explicit `MIGRATION:` note in the hint, for example:
    ```bash
    gmuse msg --hint "migrate with 'psql -f migrations/0002_add_user_email.sql'; no downtime expected"
    ```

*   **Repository instructions (optional)**

    `gmuse` injects these instructions directly into the model prompt so the LLM knows to include required metadata when the diff indicates it's needed. For example, in `pyproject.toml`:
    ```toml
    [tool.gmuse.instructions]
    instructions = [
      "When migration files change, include: MIGRATION: <short note> in the commit body.",
      "For user-visible changes, include: changelog: <one-line summary>.",
      "Tag integration-test commits with: integration-test: true"
    ]
    ```

*   **Task template** (default freeform):

    The format's task prompt (Conventional/Gitmoji/Freeform) — selected via `--format` or your config — is **included in the constructed prompt** by `gmuse`. You do not need to provide a separate template.

### 2. The Context Assembly
`gmuse` constructs a structured prompt using three distinct layers:

1.  **Instructions (System Prompt)**: The "Expert Developer" persona and guidelines (use imperative mood, focus on WHAT and WHY, etc.). See `SYSTEM_PROMPT` in `src/gmuse/prompts.py`.
2.  **Evidence (Context in User Prompt)**: The LLM is **explicitly given** your recent commits as style examples, your `--hint`, and any repository instructions. It doesn't infer patterns from nothing—it has concrete examples like `feat(db): add connection pooling` to reproduce.
3.  **Task Template**: The format-specific instructions (Conventional/Gitmoji/Freeform) are included in the constructed prompt. For Conventional, this includes the allowed types (`feat`, `fix`, etc.) and format rules.

This assembly happens in `build_prompt()` (see `src/gmuse/prompts.py`), which returns the `(system_prompt, user_prompt)` tuple sent to the LLM.

### 3. The Assembled Prompts

For this example, the assembled prompts would look like:

**System Prompt:**
```text
You are an expert commit message generator. Your role is to analyze code changes
and produce clear, informative commit messages...
```

**User Prompt:**
````text
Recent commits for style reference:
- feat(db): add connection pooling
- fix(api): handle invalid auth token
- chore(release): prepare v1.3.2 release
- perf(cache): reduce session serialization overhead
- fix(auth): validate token expiry in middleware

Repository instructions:
```
When migration files change, include: MIGRATION: <short note> in the commit body.
For user-visible changes, include: changelog: <one-line summary>.
Tag integration-test commits with: integration-test: true
```

Staged changes summary:
- Files changed: 1
- Lines added: 2
- Lines removed: 0

Diff:
```
diff --git a/migrations/0002_add_user_email.sql b/migrations/0002_add_user_email.sql
new file mode 100644
+CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, user_email VARCHAR(255));
+ALTER TABLE users ADD COLUMN user_email VARCHAR(255);
```

---

Generate a commit message following Conventional Commits specification.
Format: type(scope): description

````

### 4. The LLM Response

Because the prompt explicitly mentions migration files and the repository instruction requires a `MIGRATION:` note, the LLM should produce both the Conventional subject and a short migration instruction in the body:

```text
feat(db): add user_email column to users table

MIGRATION: run `psql -f migrations/0002_add_user_email.sql`; no downtime expected.
```

### 5. Validation

Before returning the message, `gmuse` runs `validate_message()` (see `src/gmuse/prompts.py`):

- ✅ **Not empty**: Message has content
- ✅ **Length check**: under the configured max (default 1000 characters)
- ✅ **Conventional format**: Matches `^(feat|fix|docs|...)(\(.+\))?: .+`
- ✅ **Migration note required**: Since migration files were detected, the body must include a `MIGRATION:` line. If missing, `gmuse` will request a retry or fail with a clear error prompting the user to add migration details.

Validation passes when all checks succeed, and the message is displayed (or copied to clipboard if `--copy` was used).

## See Also

*   [Privacy & Security](privacy.md): Learn how we keep your code safe.
*   [LLM Providers](llm_providers.md): Supported models and how to configure them.
*   [Configuration](../how_to/configuration.md): Customize how `gmuse` behaves in your project.
