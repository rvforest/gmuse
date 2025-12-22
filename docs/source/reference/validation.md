# Validation Rules

This reference describes the exact validation checks `gmuse` performs on generated commit messages, the canonical error messages produced when checks fail, and minimal examples.

## Purpose

Validation ensures generated messages conform to configured formats and constraints before being accepted as commit messages.

## Validation checks

| Check | Rule | Canonical error message |
|-------|------|-------------------------|
| **Empty** | Message must not be empty or whitespace-only | `Generated message is empty` |
| **Length** | Message length must be <= 1000 characters | `Message too long: {n} characters (max 1000)` |
| **Conventional** | Must match the regex `^(feat|fix|docs|style|refactor|test|chore)(\(.+\))?: .+` (case-sensitive) | `Message does not match Conventional Commits format` |
| **Gitmoji** | Message must start with an emoji followed by a space (e.g. `✨ Add feature`) | `Message does not start with an emoji` |

> Note: The Conventional regex above is enforced when `--format conventional` (or equivalent config) is selected. When using `--format freeform`, the Conventional check is skipped.

## Examples

Passing examples:

- Conventional:

```text
feat(api): add token exchange endpoint
```

- Gitmoji:

```text
✨ add token exchange endpoint
```

Failing examples:

- Empty message:

```text

```

- Too long (example snippet):

```text
<Message with 1200 characters...>
```

- Conventional mismatch:

```text
Added new feature without type prefix
# Error: Message does not match Conventional Commits format
```

- Gitmoji missing:

```text
add new feature
# Error: Message does not start with an emoji
```

## Configurable limits

- **Max length:** 1000 characters (not currently configurable via CLI; see configuration docs for any provider-level limits and future extension notes).

## Troubleshooting & Fixes

For step-by-step fixes, examples, and guidance on how to adjust prompts or use `--hint` to guide the model toward a valid message, see the [Troubleshooting guide](../how_to/troubleshooting.md).

## See also

- Troubleshooting: [Troubleshooting](../how_to/troubleshooting.md)
- Explain: [How it Works](../explanation/how_it_works.md)
- Configuration: [Configuration](../reference/configuration.md)
