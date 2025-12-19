# Configuration

gmuse can be configured via environment variables or a configuration file.

## Configuration File

gmuse looks for a configuration file in the following locations:
1. `pyproject.toml` (under `[tool.gmuse]`)
2. `.gmuse.toml`
3. `gmuse.toml`

## Options

### LLM Provider

Set the LLM provider to use.

```toml
[tool.gmuse]
provider = "openai"
```

### Model

Set the specific model to use.

```toml
[tool.gmuse]
model = "gpt-4o"
```

## Environment Variables

- `GMUSE_PROVIDER`: Override the provider.
- `GMUSE_MODEL`: Override the model.
- `OPENAI_API_KEY`: API key for OpenAI.
- `ANTHROPIC_API_KEY`: API key for Anthropic.
