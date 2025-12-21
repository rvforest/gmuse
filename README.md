<!-- markdownlint-disable MD033 MD041 -->
<div align="left">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/rvforest/gmuse/main/docs/source/_static/logo/gmuse-logo-dark.png" width="250">
<img alt="gmuse Logo" src="https://raw.githubusercontent.com/rvforest/gmuse/main/docs/source/_static/logo/gmuse-logo-light.png" width="250">
  </picture>
</div>

# gmuse

[![GitHub](https://img.shields.io/badge/GitHub-rvforest%2Fgmuse-blue?logo=github)](https://github.com/rvforest/gmuse)
[![Read the Docs](https://img.shields.io/readthedocs/gmuse)](https://gmuse.readthedocs.io)

[![Checks](https://img.shields.io/github/check-runs/rvforest/gmuse/main)](https://github.com/rvforest/gmuse/actions/workflows/run-checks.yaml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/rvforest/gmuse/graph/badge.svg?token=JXB4LR2241)](https://codecov.io/gh/rvforest/gmuse)

[![PyPI](https://img.shields.io/pypi/v/gmuse.svg)](https://pypi.org/project/gmuse/)
[![Python Versions](https://img.shields.io/pypi/pyversions/gmuse.svg)](https://pypi.org/project/gmuse/)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

AI generated git commit messages in the shell using LLMs.

## Highlights

- **AI-powered shell completions (zsh, experimental)** — context-aware suggestions for `git commit -m` that help you generate commit messages faster.
- **Fast, configurable message generation** — generate high‑quality commit messages via the CLI with customizable prompts, models, and provider settings.

## Quickstart

1. Install gmuse (see Installation below).
2. Ensure your LLM provider API key is set (e.g., `OPENAI_API_KEY`).
3. Load completions: `eval "$(gmuse completions zsh)"`
4. Stage changes: `git add .`
5. Test: `git commit -m <TAB>` — gmuse will suggest a message; confirm to use it.
6. Alternatively, generate a commit message directly: `gmuse msg`
7. Preview the prompt without calling LLM: `gmuse msg --dry-run`

See [Completions docs](https://gmuse.readthedocs.io/en/latest/getting_started/completions.html) for configuration and how to persist the completion across sessions.

## Installation

```bash
# Basic installation (works with OpenAI, Anthropic, Azure, Cohere out of the box)
pip install gmuse

# With clipboard support
pip install gmuse[clipboard]

# With Gemini support
pip install gmuse[gemini]
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

## Zsh completions (experimental)

Generate a Zsh completion script that provides AI-powered commit message
suggestions for `git commit -m`.

Quick install:

```bash
# Add to your ~/.zshrc so the completion is loaded on shell startup
eval "$(gmuse completions zsh)"
```

Configuration:

- `GMUSE_COMPLETIONS_ENABLED` (default `true`) — enable/disable completions
- `GMUSE_COMPLETIONS_TIMEOUT` (default `3.0`) — generation timeout in seconds
- `GMUSE_COMPLETIONS_CACHE_TTL` (default `30`) — cache TTL in seconds

See the documentation for details: https://gmuse.readthedocs.io/en/latest/getting_started/completions.html
