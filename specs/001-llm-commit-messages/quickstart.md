# Quickstart: LLM-Powered Commit Messages

**Feature**: 001-llm-commit-messages
**Date**: 2025-11-28
**Audience**: Developers using gmuse for the first time

## Quick Start (60 seconds)

### 1. Install gmuse

```bash
pip install gmuse[llm]
```

The `[llm]` extra includes LiteLLM for LLM provider support.

### 2. Set API Key

```bash
export OPENAI_API_KEY="sk-..."
# Or for Anthropic:
# export ANTHROPIC_API_KEY="sk-ant-..."
```

### 3. Stage Changes and Generate

```bash
cd your-git-repo
git add .
gmuse
```

That's it! gmuse will generate a commit message based on your staged changes.

## Basic Workflows

### Standard Usage

```bash
# Make changes to your code
vim src/auth.py

# Stage the changes
git add src/auth.py

# Generate commit message
gmuse

# Output (example):
# Add JWT token validation to authentication middleware
```

### With a Hint

Provide context for specific commits:

```bash
gmuse --hint "breaking change in API"

# Output (example):
# BREAKING CHANGE: Modify authentication API to require JWT tokens
```

### Copy to Clipboard

Automatically copy the message for easy pasting:

```bash
gmuse --copy

# Output:
# Add user profile endpoint
# (also copied to clipboard)
```

### Different Formats

#### Conventional Commits

```bash
gmuse --format conventional

# Output:
# feat(auth): add JWT token validation
```

#### Gitmoji Style

```bash
gmuse --format gitmoji

# Output:
# ✨ Add user profile endpoint
```

## Configuration (Optional)

Create `~/.config/gmuse/config.toml` to set defaults:

```toml
# Automatically copy to clipboard
copy_to_clipboard = true

# Use Conventional Commits format by default
format = "conventional"

# Use GPT-4 instead of auto-detected model
model = "gpt-4"

# Include more commit history for style context
history_depth = 10
```

Now you can just run `gmuse` without flags:

```bash
gmuse  # Uses your configured defaults
```

## Repository-Level Instructions

Add a `.gmuse` file to your repository root for project-specific guidance:

```bash
# In your repo root
echo "Always reference ticket numbers from branch names" > .gmuse
git add .gmuse
git commit -m "docs: add gmuse instructions"
```

Now all team members will get consistent commit messages:

```bash
# On branch PROJ-123-add-feature
gmuse

# Output:
# feat: add user authentication (PROJ-123)
```

## Learning from Your Edits (Opt-in)

Enable learning to improve message quality over time:

```bash
# In ~/.config/gmuse/config.toml
echo "learning_enabled = true" >> ~/.config/gmuse/config.toml
```

When learning is enabled:
1. Generated messages are recorded
2. If you edit them, the final version is saved
3. Future generations use your edits as examples

*(Note: v1 requires manual feedback recording; v1.1 will automate via git hooks)*

## Common Use Cases

### Quick Fixes

```bash
git add .
gmuse --format conventional

# Output: fix(api): handle null pointer in user endpoint
git commit -m "$(gmuse --format conventional)"
```

### Large Feature

```bash
# Stage only related files
git add src/auth/*.py

gmuse --hint "new authentication system"

# Output: feat(auth): implement JWT-based authentication system
```

### Documentation Update

```bash
git add README.md
gmuse --format gitmoji

# Output: 📝 Update installation instructions
```

### Multiple Small Commits

```bash
# Commit file by file with contextual messages
git add src/models/user.py
gmuse | git commit -F -

git add src/api/auth.py
gmuse | git commit -F -

git add tests/test_auth.py
gmuse --format conventional | git commit -F -
```

## Troubleshooting

### "Not a git repository"

```bash
# Make sure you're inside a git repo
git init  # If starting new project
```

### "No staged changes found"

```bash
# Stage your changes first
git add <files>
```

### "No API key configured"

```bash
# Set your provider's API key
export OPENAI_API_KEY="sk-..."
```

### "Failed to reach LLM provider"

```bash
# Check network connection
# Or increase timeout:
export GMUSE_TIMEOUT=60
gmuse
```

### Message Format Not as Expected

```bash
# Explicitly set format
gmuse --format conventional

# Or set in config
echo 'format = "conventional"' >> ~/.config/gmuse/config.toml
```

## Advanced Tips

### Alias for Quick Commits

```bash
# Add to ~/.zshrc or ~/.bashrc
alias gc='git commit -m "$(gmuse)"'

# Now just:
git add .
gc
```

### Pre-commit Hook (Optional)

Generate message automatically when committing:

```bash
# .git/hooks/prepare-commit-msg
#!/bin/sh
if [ -z "$2" ]; then
    gmuse > "$1"
fi
chmod +x .git/hooks/prepare-commit-msg
```

### Review Before Committing

```bash
# Generate and review
MESSAGE=$(gmuse)
echo "Generated: $MESSAGE"
read -p "Use this message? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git commit -m "$MESSAGE"
fi
```

### Different Models for Different Situations

```bash
# Quick fixes with fast/cheap model
gmuse --model gpt-3.5-turbo

# Important commits with better model
gmuse --model gpt-4
```

## Next Steps

- **Learn more**: Read the [full documentation](https://gmuse.readthedocs.io)
- **Configuration reference**: See [configuration guide](https://gmuse.readthedocs.io/config)
- **Contributing**: Check [development guide](https://gmuse.readthedocs.io/development)

## Getting Help

- **Documentation**: https://gmuse.readthedocs.io
- **Issues**: https://github.com/rvforest/gmuse/issues
- **Discussions**: https://github.com/rvforest/gmuse/discussions

## What's NOT Supported (Yet)

- **Commit splitting**: Automatically splitting large changes into logical commits (planned for v1.1)
- **IDE integration**: Plugins for VS Code, JetBrains, etc. (planned for v1.2)
- **Git hooks auto-install**: One-command hook setup (planned for v1.1)
- **Custom templates**: User-defined message templates (planned for v2.0)

For these features, check the [roadmap](https://github.com/rvforest/gmuse/blob/main/planning/roadmap.md).
