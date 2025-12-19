# LLM Providers

gmuse supports a wide range of LLM providers via LiteLLM.

## Supported Providers

- **OpenAI**: GPT-4, GPT-3.5
- **Anthropic**: Claude 3
- **Google**: Gemini
- **Cohere**: Command
- **Azure**: Azure OpenAI
- **Bedrock**: AWS Bedrock
- **HuggingFace**: Various models

## Configuration

To use a specific provider, set the `provider` option in your configuration or use the `GMUSE_PROVIDER` environment variable.

Ensure you have the necessary API keys set in your environment (e.g., `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`).
