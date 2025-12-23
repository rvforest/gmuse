# Configure gmuse

This guide shows you how to configure gmuse for common use cases. For complete configuration options, see the [Configuration Reference](../reference/configuration.md).

## Set up your first configuration

Create a configuration file to set persistent preferences:

1. Create the config directory if it doesn't exist:
   ```bash
   mkdir -p ~/.config/gmuse
   ```

2. Create `~/.config/gmuse/config.toml` with your preferences:
   ```toml
   model = "gpt-4o-mini"
   format = "conventional"
   history_depth = 10
   ```

3. Test your configuration:
   ```bash
   gmuse info
   ```

You should see your configured model and settings displayed.

## Switch between LLM providers

To use a different provider, set the appropriate API key and optionally specify the provider:

**For OpenAI:**
```console
$ export OPENAI_API_KEY="sk-..."
$ gmuse msg
```

**For Anthropic Claude:**
```console
$ export ANTHROPIC_API_KEY="sk-ant-..."
$ gmuse msg --provider anthropic --model claude-3-5-sonnet-20241022
```

**For Google Gemini:**
```console
$ export GEMINI_API_KEY="..."
$ gmuse msg --provider gemini
```

To make a provider your default, add it to your config file:
```toml
provider = "anthropic"
model = "claude-3-5-sonnet-20241022"
```

## Change commit message format

To use Conventional Commits format:

**For one commit:**
```console
$ gmuse msg --format conventional
```

**Persistently:**
```toml
# ~/.config/gmuse/config.toml
format = "conventional"
```

**For gitmoji style:**
```toml
format = "gitmoji"
```

## Adjust history context

Control how many past commits gmuse uses as style examples:

**Use more history for better style matching:**
```toml
history_depth = 15
```

**Disable history context:**
```toml
history_depth = 0
```

**Override for a single command:**
```console
$ gmuse msg --history-depth 20
```

## Tune LLM generation parameters

Control how the AI generates messages:

### Temperature

Temperature controls randomness (0.0 = deterministic, 2.0 = very creative):

**For deterministic CI/CD environments:**
```toml
temperature = 0.0
```

**For creative messages (default is 0.7):**
```toml
temperature = 1.2
```

**Override for a single command:**
```console
$ gmuse msg --temperature 0.3
```

### Maximum tokens

Limit the length of generated messages:

```toml
max_tokens = 200  # Shorter messages
```

```console
$ gmuse msg --max-tokens 100
```

### Diff size limits

Control how much code context is sent to the LLM:

```toml
max_diff_bytes = 50000  # Allow larger diffs (default: 20000)
```

```console
$ gmuse msg --max-diff-bytes 10000  # Smaller limit
```

**Use case:** Large diffs may exceed API limits or increase costs. Adjust this based on your needs.

### Other tunable parameters

Configure via environment variables or config file:

```toml
max_message_length = 500    # Maximum commit message length (default: 1000)
chars_per_token = 4         # Token estimation heuristic (default: 4)
```

```console
$ export GMUSE_MAX_MESSAGE_LENGTH=500
$ export GMUSE_CHARS_PER_TOKEN=3
```

## Enable clipboard copying

To automatically copy messages to your clipboard:

1. Install the clipboard extra:
   ```console
   $ pip install 'gmuse[clipboard]'
   ```

2. Enable in config:
   ```toml
   copy_to_clipboard = true
   ```

Or use the `--copy` flag for one-time copying:
```console
$ gmuse msg --copy
```

## Set project-specific instructions

For team-wide commit message conventions, create a `.gmuse` file in your repository root:

1. Create `.gmuse` in your project:
   ```console
   $ cat > .gmuse << 'EOF'
   All commit messages must reference a Jira ticket in the format [PROJ-123].
   Keep subject lines under 50 characters.
   Use present tense for all messages.
   EOF
   ```

2. Commit the file so the team can use it:
   ```console
   $ git add .gmuse
   $ git commit -m "docs: add commit message guidelines"
   ```

Now gmuse will include these instructions in every prompt for this repository.

## Increase timeout for slow networks

If you're experiencing timeout errors:

**For all commands:**
```toml
timeout = 120
```

**For one command:**
```console
$ gmuse msg  # Uses GMUSE_TIMEOUT if set
```

Or set via environment:
```console
$ export GMUSE_TIMEOUT=120
$ gmuse msg
```

## Enable debug logging

To troubleshoot issues:

**Temporary debug mode:**
```console
$ GMUSE_DEBUG=1 gmuse msg
```

**Debug to file:**
```console
$ export GMUSE_LOG_FILE=~/.cache/gmuse/debug.log
$ export GMUSE_DEBUG=1
$ gmuse msg
```

> **Warning:** Debug logs may contain your code diffs and prompts. Don't enable in sensitive environments.

## Override config for testing

Test different settings without changing your config file:

```console
# Try a different model
$ gmuse msg --model gpt-4o --dry-run

# Test conventional format
$ gmuse msg --format conventional --dry-run
# Try with no history
$ gmuse msg --history-depth 0 --dry-run
```

The `--dry-run` flag shows you the prompt without calling the LLM.

## Check your configuration

To see what settings are active:

```console
$ gmuse info
```

This shows:
- Resolved model name
- Detected provider
- Which API keys are set
- Environment variables in use
