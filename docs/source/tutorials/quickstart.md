# Quick Start

This quick start shows the minimal steps to install gmuse, configure a provider,
and generate an AI-powered commit message from staged git changes.

## Prerequisites

- Python 3.10 or newer
- A git repository (or `git init` a new one)
- An LLM provider API key (OpenAI, Anthropic, Google Gemini, etc.) for your model of choice

## Install

Install gmuse with pip:

```console
$ pip install gmuse
```

For optional extras (clipboard support), see the
[Installation](../how_to/installation.md) guide for details.

## Configure Provider Credentials

Set your provider API key in the environment (for example, `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`), or configure defaults in `~/.config/gmuse/config.toml`. See the [LiteLLM](https://docs.litellm.ai/docs/providers) documentation for the complete list of supported providers and authentication requirements.

## Generate Your First Commit Message

Create a git repository and some changes, stage them, then run `gmuse msg`:

```console
$ git init example
$ cd example
$ echo "print('hello world')" > hello.py
$ git add hello.py
$ gmuse msg
```

You should see a generated commit message printed to stdout. Example output (your
message will vary):

```text
feat: add hello.py with simple print

A short summary of the changes with optional details following.
```

### Copy to Clipboard
To copy automatically for a single invocation, pass `--copy` to `gmuse msg`; to enable persistent copying, set `copy_to_clipboard = true` in your config file (see the [Configuration guide](../how_to/configuration.md)). Clipboard support requires the optional `gmuse[clipboard]` extra.

## Try shell completions

Load completions into your shell (Zsh example):

```console
# load completions into current shell
eval "$(gmuse git-completions zsh)"
```

Then use completion during `git commit -m <TAB>` to insert a suggested message. For more shells and installation instructions, see the Completions guide in the docs. Completions insert the suggestion directly into `git commit -m`.

## Common Options

Quick examples used in this guide:

- `--dry-run`: Preview the assembled prompt without contacting a provider
- `--format <freeform|conventional|gitmoji>`: Choose an output format
- `--copy`: Copy the generated message to your clipboard


See the CLI Reference for the full list of options and examples (`../reference/cli.md`).

## Troubleshooting & Debugging

If gmuse can't detect your provider or model, run `gmuse info` to inspect resolved configuration. If you see `No staged changes`, run `git add` to stage files; see the Troubleshooting guide for more diagnostic tips (`../how_to/troubleshooting.md`).

## Tips

- Use `--format conventional` for Conventional Commits compatible messages when
	your project follows semantic commit styles.
- Use `--hint` to influence the tone or focus of the message (e.g.,
	"emphasize performance" or "security fix").
- Set `GMUSE_MODEL` in your environment to pin a model for repeated usage.

## Next Steps

- See the Installation page for provider-specific setup and supported models.
- Consult the API Reference to integrate gmuse programmatically.

Happy committing! 🎉
