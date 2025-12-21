# Installation

## Basic Installation

gmuse requires Python 3.10 or higher.

```bash
pip install gmuse
```

This installs gmuse with support for the most common LLM providers (OpenAI, Anthropic, Azure, Cohere) out of the box.

## Provider-Specific Installation

Some LLM providers require additional packages. Install the appropriate extras for your provider:

```bash
# Clipboard support (copy generated messages)
pip install gmuse[clipboard]

# Google Gemini
pip install gmuse[gemini]

# AWS Bedrock
pip install gmuse[bedrock]

# Google Vertex AI
pip install gmuse[vertex]

# HuggingFace models
pip install gmuse[huggingface]
```

## Provider Support Matrix

| Provider | Extra Package Required | Works Out of Box |
|----------|----------------------|------------------|
| OpenAI | None | ✅ |
| Anthropic (Claude) | None | ✅ |
| Azure OpenAI | None | ✅ |
| Cohere | None | ✅ |
| Google Gemini | `[gemini]` | ❌ |
| AWS Bedrock | `[bedrock]` | ❌ |
| Google Vertex AI | `[vertex]` | ❌ |
| HuggingFace | `[huggingface]` | ❌ |

gmuse supports 100+ LLM providers via [LiteLLM](https://docs.litellm.ai/docs/providers). See the LiteLLM documentation for the complete list.

## Development Installation

For contributing to gmuse:

```bash
git clone https://github.com/rvforest/gmuse.git
cd gmuse
uv sync  # Installs all dependencies including dev tools
```

## Google Gemini vs Vertex AI

Google provides two main ways to access Gemini models:

- **Google AI Studio (Gemini API key)** — Use the Gemini API key (`GEMINI_API_KEY`) and select a `gemini-...` model; this is usually what you want for personal testing.
- **Vertex AI (service account / Application Default Credentials)** — Use Vertex for enterprise scenarios; you must provide ADC via `GOOGLE_APPLICATION_CREDENTIALS` or a configured default gcloud credential.

If you see errors like `Your default credentials were not found` it likely means the selected model requires Vertex credentials (model name starts with `vertex_...` or `vertex_ai/...`) but ADC isn't configured. Either:

1. Switch to a Gemini model and set `GEMINI_API_KEY`:
```bash
export GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
export GMUSE_MODEL="gemini/gemini-flash-lite-latest"
```

2. Or configure ADC for Vertex AI:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
export GMUSE_MODEL="vertex_ai/gemini/gemini-flash-lite-latest"
```

Pick the path that matches how you want to authenticate. gmuse defaults to a Gemini model for user convenience (unless you explicitly set `vertex_` in your model value).
