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
```bash
export OPENAI_API_KEY="sk-..."
gmuse msg
```

**For Anthropic Claude:**
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
gmuse msg --provider anthropic --model claude-3-5-sonnet-20241022
```

**For Google Gemini:**
```bash
export GEMINI_API_KEY="..."
gmuse msg --provider gemini
```

To make a provider your default, add it to your config file:
```toml
provider = "anthropic"
model = "claude-3-5-sonnet-20241022"
```

## Change commit message format

To use Conventional Commits format:

**For one commit:**
```bash
gmuse msg --format conventional
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
```bash
gmuse msg --history-depth 20
```

## Enable clipboard copying

To automatically copy messages to your clipboard:

1. Install the clipboard extra:
   ```bash
   pip install 'gmuse[clipboard]'
   ```

2. Enable in config:
   ```toml
   copy_to_clipboard = true
   ```

Or use the `--copy` flag for one-time copying:
```bash
gmuse msg --copy
```

## Set project-specific instructions

For team-wide commit message conventions, create a `.gmuse` file in your repository root:

1. Create `.gmuse` in your project:
   ```bash
   cat > .gmuse << 'EOF'
   All commit messages must reference a Jira ticket in the format [PROJ-123].
   Keep subject lines under 50 characters.
   Use present tense for all messages.
   EOF
   ```

2. Commit the file so the team can use it:
   ```bash
   git add .gmuse
   git commit -m "docs: add commit message guidelines"
   ```

Now gmuse will include these instructions in every prompt for this repository.

## Increase timeout for slow networks

If you're experiencing timeout errors:

**For all commands:**
```toml
timeout = 120
```

**For one command:**
```bash
gmuse msg  # Uses GMUSE_TIMEOUT if set
```

Or set via environment:
```bash
export GMUSE_TIMEOUT=120
gmuse msg
```

## Enable debug logging

To troubleshoot issues:

**Temporary debug mode:**
```bash
GMUSE_DEBUG=1 gmuse msg
```

**Debug to file:**
```bash
export GMUSE_LOG_FILE=~/.cache/gmuse/debug.log
export GMUSE_DEBUG=1
gmuse msg
```

> **Warning:** Debug logs may contain your code diffs and prompts. Don't enable in sensitive environments.

## Override config for testing

Test different settings without changing your config file:

```bash
# Try a different model
gmuse msg --model gpt-4o --dry-run

# Test conventional format
gmuse msg --format conventional --dry-run

# Try with no history
gmuse msg --history-depth 0 --dry-run
```

The `--dry-run` flag shows you the prompt without calling the LLM.

## Check your configuration

To see what settings are active:

```bash
gmuse info
```

This shows:
- Resolved model name
- Detected provider
- Which API keys are set
- Environment variables in use
