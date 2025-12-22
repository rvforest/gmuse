# Installation

## Basic Installation

gmuse requires Python 3.10 or higher.

::::{tab-set}

:::{tab-item} uv
:sync: uv

```console
uv tool install gmuse
```

:::

:::{tab-item} pipx
:sync: pipx

```console
pipx install gmuse
```

:::

:::{tab-item} pip
:sync: pip

```console
pip install gmuse
```

:::

::::

## Extras

| Extra     | Purpose |
  -----     | ------- |
| clipboard | Automatically copy gmuse suggestions to clipboard |

```bash
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
