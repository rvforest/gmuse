````markdown
# Prompt Context Contract: `max_chars`

## When included

- If `max_chars` is configured (non-null), the generated user prompt MUST include a clear, explicit rule describing the maximum message length.

## Required wording

The prompt MUST include the following information:

- The configured limit value
- The unit (“characters”)

Example (exact wording may differ, meaning must match):

- `Maximum length: 120 characters.`

## Conflict avoidance

- When `max_chars` is configured, the user prompt MUST NOT contain a conflicting length requirement (e.g., Conventional Commits “under 100 characters”) that would contradict the configured limit.

## Validation alignment

- If the LLM output exceeds `max_chars`, the run MUST fail with an error.
- The error MUST include both:
  - actual length
  - configured limit

````
