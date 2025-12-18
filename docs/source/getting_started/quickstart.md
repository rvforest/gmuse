# Quick Start

This quick start shows the minimal steps to install gmuse, configure a provider,
and generate an AI-powered commit message from staged git changes.

## Prerequisites

- Python 3.10 or newer
- A git repository (or `git init` a new one)
- An LLM provider API key (OpenAI, Anthropic, Google Gemini, etc.) for your model of choice

## Install

Install gmuse with pip (the simplest option):

```bash
pip install gmuse
```

For optional extras (clipboard, provider-specific integrations, etc.), see the
[Installation](installation.md) guide for details and the provider support matrix.

## Configure Provider Credentials

Provider credentials vary; many use a single API key environment variable. For a
quick example (OpenAI/Anthropic):

```bash
export OPENAI_API_KEY="sk-..."       # OpenAI
export ANTHROPIC_API_KEY="sk-ant..." # Anthropic
```

You can also set defaults via the configuration file at `~/.config/gmuse/config.toml`.
See the [Installation](installation.md) page for provider-specific setup (Gemini,
Vertex, Bedrock, etc.) and additional credentials required by some providers.

## 🧪 Generate Your First Commit Message

Create a git repository and some changes, stage them, then run `gmuse msg`:

```bash
git init example
cd example
echo "print('hello world')" > hello.py
git add hello.py
gmuse msg
```

You should see a generated commit message printed to stdout. Example output (your
message will vary):

```text
feat: add hello.py with simple print

A short summary of the changes with optional details following.
```

## Try shell completions

Install and load completions (Zsh example), then try a quick completions run:

```bash
# load completions into current shell
eval "$(gmuse completions zsh)"
```

```zsh
git commit -m <TAB>
# gmuse will generate a suggested commit message and insert it into the -m argument
```

If you want the message copied to your clipboard automatically, either pass the
`--copy` flag or set `copy_to_clipboard = true` in your config file:

```bash
gmuse msg --copy
```

## ✨ Common Options

- `--hint` / `-h`: Give extra guidance for the generated message
- `--format` / `-f`: Output format: `freeform`, `conventional`, or `gitmoji`
- `--model` / `-m`: Use a specific model for this invocation (overrides env/config)
- `--provider`: Explicit provider override for edge cases
- `--history-depth`: Number of prior commits to use for style context (0–50)

Examples:

```bash
gmuse msg --hint "fix security bug" --format conventional
gmuse msg --model "claude-3-opus-20240229" --provider anthropic
gmuse msg --history-depth 10
```

## ️Troubleshooting & Debugging

- If gmuse can't detect your provider or model, run `gmuse info` to view
	resolved environment values and merged configuration:

```bash
gmuse info
```

- If gmuse reports "No staged changes", remember to `git add` the files you want
	to commit.
- If your diff is large, gmuse may truncate the diffs to fit model token limits;
	it will warn you and still produce a concise message.

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
