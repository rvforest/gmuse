# Host a local model (maximum privacy)

This guide shows how to run `gmuse` against a **local** LLM so your prompts and responses stay on your machine.

- `gmuse` uses [LiteLLM](https://docs.litellm.ai/docs/) under the hood.
- Local hosting means **you** operate the model runtime (no gmuse backend servers).

If you haven't already, read the privacy overview: [Privacy & Security](../explanation/privacy.md).

## When to use a local model

Local hosting is a good fit when you want:

- Maximum privacy (no third-party API calls)
- Offline usage (after the model is downloaded)
- Predictable costs (no per-request billing)

It may be a poor fit when you need:

- The highest quality for complex reasoning (local models may be weaker than frontier hosted models)
- Very large context windows
- Zero maintenance (you are responsible for updates and security)

## Security checklist (read first)

If you follow only one section, follow this one.

- **Bind locally by default**: keep the inference server on `127.0.0.1` (localhost).
- **Do not expose the port publicly** unless you understand the risks.
- **If you must access it remotely**:
  - Put it behind authentication.
  - Use TLS.
  - Restrict access (VPN, firewall rules, allowlists).
- **Disable debug logging** in sensitive environments:
  - Avoid `GMUSE_DEBUG=1` and DEBUG-level logs because prompts/diffs may be written to logs.
- **Treat model downloads like binaries**:
  - Prefer official sources.
  - Keep the runtime and models updated.
  - Review licensing before redistribution or commercial use.

## Recommended “golden path”: Ollama + LiteLLM

Ollama is a simple local LLM runtime. LiteLLM supports Ollama models via the `ollama/` (or `ollama_chat/`) model prefix.

### 1) Install and run Ollama

Follow Ollama’s official install instructions for your OS:

- https://ollama.com/download

Ensure the Ollama server is running and listening on localhost (default: `http://localhost:11434`).

### 2) Pull a model

Pick a model that’s strong at short, structured text generation.

Examples (choose one):

```console
$ ollama pull qwen2.5-coder
```

```console
$ ollama pull llama3.1
```

Notes:

- Smaller models (around 7B–8B) are typically a good speed/quality balance for commit messages.
- Model names vary by runtime; use `ollama list` to see what you have locally.

### 3) Point gmuse at the local model

You can configure a local model either temporarily (environment) or persistently (config file).

**Option A — Environment variable (one shell session):**

```console
$ export GMUSE_MODEL="ollama/qwen2.5-coder"
$ gmuse msg
```

**Option B — Config file (persistent):**

Add to `~/.config/gmuse/config.toml`:

```toml
model = "ollama/qwen2.5-coder"
```

Then run:

```console
$ gmuse msg
```

### 4) Verify configuration

`gmuse info` prints the resolved model and provider heuristics:

```console
$ gmuse info
```

If your provider is detected as `ollama`, your `GMUSE_MODEL` is being interpreted as a local runtime model.

## Generalize to other local backends

Ollama is the simplest path, but it’s not the only one.

Two common patterns work well with `gmuse`:

### Pattern A — Use a LiteLLM provider prefix

If LiteLLM supports your local backend directly, set `GMUSE_MODEL` to the appropriate provider-prefixed model name.

Examples:

- `ollama/<model>`
- `ollama_chat/<model>` (often better chat-style responses)

See the LiteLLM providers list:

- https://docs.litellm.ai/docs/providers

### Pattern B — Use an OpenAI-compatible endpoint (advanced)

Some local servers expose an OpenAI-compatible API.

Best practices for this approach:

- Prefer a LiteLLM provider that matches your backend (when available) instead of the generic OpenAI-compatible route.
- If your OpenAI-compatible client requires an API key even locally, use a non-sensitive placeholder and enable authentication on the server if it’s reachable beyond localhost.

LiteLLM reference:

- https://docs.litellm.ai/docs/providers/openai_compatible

## Troubleshooting

### gmuse says no provider is configured

Run:

```console
$ gmuse info
```

Common causes:

- `GMUSE_MODEL` isn’t set and no provider API key env var is set.
- `GMUSE_MODEL` is set to a value LiteLLM doesn’t recognize.

### Connection errors

If you see errors connecting to Ollama:

- Verify the server is running (default address `http://localhost:11434`).
- Confirm the model exists locally: `ollama list`.
- Ensure you can reach the server from the same environment you run `gmuse` from.

### Output is too long or too random

Tune these settings:

- Lower temperature for more deterministic messages
- Reduce max tokens for shorter outputs

Example config:

```toml
temperature = 0.2
max_tokens = 200
```

See also: [Configure gmuse](configuration.md) and the [Configuration Reference](../reference/configuration.md).
