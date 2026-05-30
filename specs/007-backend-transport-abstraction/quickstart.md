````markdown
# Quickstart: Backend and Transport Abstraction

This feature makes backend selection explicit while preserving the simple direct-backend path for users who already have one compatible direct backend configured.

## 1. Existing single-backend setup keeps working

If you already have one supported direct backend configured, `gmuse` continues to auto-resolve that backend and its default model.

Example:

```bash
export OPENAI_API_KEY="example-openai-key" # pragma: allowlist secret
gmuse msg
```

Expected behavior:

- gmuse resolves the `openai` backend automatically
- gmuse resolves the maintained default model for that backend if no model is supplied

## 2. Select a backend explicitly

You can choose the active backend independently of the model.

These examples assume the matching backend credential is already set; the Anthropic example uses `ANTHROPIC_API_KEY`.

### CLI flag

```bash
export ANTHROPIC_API_KEY="example-anthropic-key" # pragma: allowlist secret
gmuse msg --backend anthropic --model claude-haiku-4-5
```

### Environment variable

```bash
export GMUSE_BACKEND=anthropic
gmuse msg
```

### Config file

```toml
backend = "anthropic"
model = "claude-haiku-4-5"
```

## 3. Ambiguous multi-backend setups fail clearly

If multiple compatible direct backends are configured and you do not provide enough information to choose one deterministically, gmuse fails with a clear error instead of guessing.

Expected recovery options:

- specify `--backend`
- set `GMUSE_BACKEND`
- choose a model that clearly names a native backend, such as a `claude-*` model for Anthropic or a `gpt-*` model for OpenAI

## 4. Diagnostics show the resolved execution context

Use diagnostic output to confirm what gmuse resolved.

Example:

```bash
gmuse info
```

Expected diagnostic content:

- active backend
- resolved model
- why that backend was selected

## 5. Backend-specific advanced controls come later

This feature reserves a backend-specific settings mechanism but does not add concrete advanced backend-specific controls yet. Future backend features will use that reserved namespace instead of adding unrelated global settings, and the current CLI/config help intentionally keeps those controls hidden until they become active.

````
