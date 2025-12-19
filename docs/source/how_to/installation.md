# Installation

## Basic Installation

gmuse requires Python 3.10 or higher.

```bash
pip install gmuse
```

## Optional Dependencies

```bash
# Clipboard support (copy generated messages)
pip install gmuse[clipboard]
```

## Provider Support

gmuse supports 100+ LLM providers via [LiteLLM](https://docs.litellm.ai/docs/providers). All providers work with the base installation - no additional packages are required.

Popular providers include:
- OpenAI
- Anthropic (Claude)
- Azure OpenAI
- Cohere
- Google Gemini
- AWS Bedrock
- Google Vertex AI
- And many more

See the LiteLLM documentation for the complete list of supported providers.

## Development Installation

For contributing to gmuse:

```bash
git clone https://github.com/rvforest/gmuse.git
cd gmuse
uv sync  # Installs all dependencies including dev tools
```
