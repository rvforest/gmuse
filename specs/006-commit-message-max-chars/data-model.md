````markdown
# Data Model: Commit Message Max Characters

## Entity: `max_chars`

**Type**: Integer or null

**Meaning**: Maximum number of characters permitted in the generated commit message.

**Default**: `null` (disabled)

**Validation**:

- If provided, MUST be an integer.
- MUST be within 1–500 inclusive.

**Character counting**:

- Character count is computed as `len(message)` (Unicode code points).
- Includes newline characters.

## Relationships

- `max_chars` interacts with existing `max_message_length`:
  - If `max_chars` is set, it becomes the effective length constraint used for prompt context and validation.
  - If `max_chars` is not set, `max_message_length` continues to control validation as it does today.

## State / Transitions

- `null` → enabled: user sets a valid integer value.
- enabled → `null`: user removes the setting (disabled).

````
