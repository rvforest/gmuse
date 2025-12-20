# Data Model: `gmuse msg --dry-run`

This feature does not introduce persistent storage. It introduces a **logical output model** for the dry-run prompt preview.

## Entities

### 1) DryRunPromptOutput

Represents what would be sent to the LLM provider, plus minimal metadata.

Fields:

- `model: str | None`
  - Meaning: Effective model name that would be used for generation.
  - Source: Merged config (CLI overrides + env + config file), as used in normal runs.

- `format: str`
  - Meaning: Message format (`freeform`, `conventional`, `gitmoji`).
  - Source: Merged config.

- `truncated: bool`
  - Meaning: Whether the staged diff was truncated.
  - Source: `GenerationContext.diff_was_truncated` (CLI already computes this).

- `system_prompt: str`
  - Meaning: System prompt content.
  - Source: `gmuse.prompts.build_prompt`.

- `user_prompt: str`
  - Meaning: User prompt content.
  - Source: `gmuse.prompts.build_prompt`.

## Validation rules

- `system_prompt` and `user_prompt` must be non-empty strings.
- `format` must be one of the supported values already accepted by prompt builder.
- `truncated` must reflect the same truncation behavior as non-dry-run execution.

## State transitions

No state machine or persistence.

- Inputs (CLI args + repo state) → prompt assembly → stdout output
