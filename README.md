<!-- markdownlint-disable MD033 MD041 -->
<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/rvforest/gmuse/main/docs/source/_static/logo/gmuse-logo-dark.png" width="500">
<img alt="gmuse Logo" src="https://raw.githubusercontent.com/rvforest/gmuse/main/docs/source/_static/logo/gmuse-logo-light.png" width="500">
  </picture>
</div>

# gmuse

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

AI generated commit messages using LLMs.

## Installation

```bash
# Basic installation (works with OpenAI, Anthropic, Azure, Cohere out of the box)
pip install gmuse

# With clipboard support
pip install gmuse[clipboard]

# With Gemini support
pip install gmuse[gemini]

# With all provider support
pip install gmuse[all]
```

## Provider Setup

gmuse supports 100+ LLM providers via LiteLLM. Most providers work out of the box, but some require additional packages:

- **OpenAI, Anthropic, Azure, Cohere**: Work immediately (no extra packages)
- **Google Gemini**: Requires `pip install gmuse[gemini]`
- **AWS Bedrock**: Requires `pip install gmuse[bedrock]`
- **HuggingFace**: Requires `pip install gmuse[huggingface]`

Set your API key:
```bash
export OPENAI_API_KEY="sk-..."          # For OpenAI
export ANTHROPIC_API_KEY="sk-ant-..."  # For Anthropic
export GOOGLE_API_KEY="..."             # For Gemini
# Or configure in ~/.config/gmuse/config.toml

CLI provider override:

```bash
# Explicitly select provider for a single command invocation
gmuse --provider gemini
gmuse --provider anthropic --model claude-3-opus-20240229
```
```
