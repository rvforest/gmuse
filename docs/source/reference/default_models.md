# Default Models

This page documents gmuse's default LLM model choices for the built-in direct backends and the rationale.

## Default mapping (economy-focused)

- **openai**: `gpt-4o-mini`
- **anthropic**: `claude-haiku-4-5`
- **cohere**: `command-light`
- **azure**: `gpt-4o-mini`
- **gemini**: `gemini/gemini-flash-lite-latest`

## Rationale

The defaults prefer smaller/light/mini/haiku variants intended to be lower-cost and
lower-latency while still providing reliable instruction-following for short
text generation tasks such as commit message generation. Once gmuse resolves the
active backend, it uses that backend's default model unless you override it with
`GMUSE_MODEL`, `backend = "..."` plus `model = "..."`, or the `--model` CLI option.

## Notes

- These defaults may be updated over time as providers introduce newer, more
  cost-efficient variants. If you need higher quality or advanced capabilities
  (e.g., long-form reasoning or large-context agents), specify a stronger
  model via `--model` or config file.
- When multiple compatible backends are configured, use `--backend` or
  `GMUSE_BACKEND` if you want to override the automatic backend selection.
