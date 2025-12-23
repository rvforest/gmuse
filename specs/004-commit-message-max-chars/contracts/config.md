````markdown
# Configuration Contract: `max_chars`

## Setting

- Key: `max_chars`
- Type: integer or null
- Default: null (disabled)
- Valid range: 1–500 inclusive

## Sources and precedence

The setting is resolved using the existing configuration merge order:

1. CLI flags (highest priority) *(if added in a future iteration)*
2. `config.toml`
3. Environment variables
4. Defaults (lowest priority)

## Environment variable

- `GMUSE_MAX_CHARS`
  - Parsed as an integer.

## Interaction with existing settings

- If `max_chars` is set, it MUST be used as the effective message-length limit for both:
  - prompt context
  - output validation

- If `max_chars` is null/unset, the system MUST behave as it does today, using existing `max_message_length` for validation.

## Errors

Invalid values MUST produce a `ConfigError` with an actionable message.

Examples:

- Non-integer: `max_chars must be an integer, got <type>`
- Out of range: `max_chars must be between 1 and 500, got <value>`

````
