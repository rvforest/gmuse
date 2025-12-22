# Troubleshooting

This page contains practical, step-by-step troubleshooting and debugging advice for `gmuse`.

Use this guide when you need to resolve common problems (timeouts, authentication failures, validation errors, rate limits, etc.) or when you want to inspect what `gmuse` would send to a provider.

## Dry-run & debugging

Use `gmuse msg --dry-run` to print the assembled prompts (`SYSTEM PROMPT` and `USER PROMPT`) without contacting any LLM provider — useful to inspect exactly what will be sent. The `--dry-run` command never calls providers and does not consume tokens.

For more detailed provider/client diagnostics, set the environment variable `GMUSE_DEBUG=1` before running gmuse; this enables LiteLLM/provider debug output. Prompts are also logged by gmuse at DEBUG level if you enable debug logging.

**Note:** If you see `No staged changes`, make sure you've staged your files with `git add`. Use `gmuse msg --dry-run` to confirm that your diff is included and to check whether gmuse warns about truncation due to model token limits.

### Dry-run example

Running `gmuse msg --dry-run` outputs the exact prompts that would be sent (truncated here for brevity):

````text
MODEL: gpt-4o-mini
FORMAT: conventional
TRUNCATED: false

SYSTEM PROMPT:
```
<system prompt content>
```

USER PROMPT:
```
<User prompt content including diff, recent commits, instructions, hint, etc.>
```
````

## Validation failures

If a generated message fails validation (empty, too long, format mismatch), try these steps:

1. Run `gmuse msg --dry-run` to inspect the prompts being sent.
2. Try a different `--format` (for example, `--format freeform` is the most permissive).
3. Adjust your `--hint` to guide the model toward a valid format (e.g., include an example or required prefix).
4. Check if your `.gmuse` instructions (or `[tool.gmuse.instructions]`) conflict with the selected format.

For the exact validation rules and canonical error messages, see the [Validation reference](../reference/validation.md).

### Examples & fixes

- "Generated message is empty": Run with `--dry-run` to confirm the prompt includes the diff and examples; try increasing `temperature` slightly or providing a clearer hint.
- "Message too long: 1200 characters (max 1000)": Reduce `max_tokens` in your provider config, or add a hint like `"Keep message under 80 characters"`.
- "Message does not match Conventional Commits format": Use `--format conventional` and add a `--hint` with an example commit message in the expected format.

## Error handling

When provider errors occur, `gmuse` displays helpful messages and exits without retrying automatically. Common error types and recovery steps:

| Error Type | Message | Recovery |
|------------|---------|----------|
| **Authentication** | `Authentication failed. Check your API key` | Verify your `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc. |
| **Timeout** | `Request timed out after 30 seconds` | Increase timeout: `export GMUSE_TIMEOUT=60` or choose a faster model |
| **Rate limit** | `Rate limit exceeded. Wait a moment and try again` | Wait and retry, or switch to a different model |
| **Network** | `Network error. Check your internet connection` | Check connectivity and retry |

> **Tip:** Set `GMUSE_DEBUG=1` to enable detailed LiteLLM/provider debug output for troubleshooting.

## See also

- Conceptual overview: [How it Works](../explanation/how_it_works.md)
- Configuration reference: [Configuration](../reference/configuration.md)
