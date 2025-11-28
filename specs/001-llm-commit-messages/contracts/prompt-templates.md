# Prompt Templates: LLM Commit Message Generation

**Feature**: 001-llm-commit-messages  
**Date**: 2025-11-28  
**Purpose**: Define prompt structure and format-specific templates for LLM interactions

## Overview

This document specifies the prompt templates used to generate commit messages. Templates are structured to maximize LLM comprehension while staying within token budgets.

## Prompt Structure

All prompts follow a three-section structure:

1. **SYSTEM**: Role definition and constraints
2. **CONTEXT**: Input data (diff, history, instructions)
3. **TASK**: Output format and requirements

## Base System Prompt

Used for all generations, regardless of format:

```
You are an expert commit message generator. Your role is to analyze code changes and produce clear, informative commit messages that help developers understand what changed and why.

Guidelines:
- Focus on WHAT changed and WHY (when obvious from diff)
- Be concise but informative
- Use technical terminology appropriately
- Avoid stating the obvious (e.g., "Updated file.py")
- Prioritize clarity over cleverness
```

## Context Section Template

```
Repository: {repo_name}

Recent commits for style reference:
{commit_history}

{repository_instructions}

{user_hint}

{learning_examples}

Staged changes summary:
- Files changed: {files_count}
- Lines added: {lines_added}
- Lines removed: {lines_removed}

Diff:
{staged_diff}
```

### Field Descriptions

- `{repo_name}`: Repository name or path (for context)
- `{commit_history}`: Last N commit messages, one per line
- `{repository_instructions}`: Content of `.gmuse` file (if exists)
- `{user_hint}`: Value of `--hint` flag (if provided)
- `{learning_examples}`: Few-shot examples from learning history (if available)
- `{files_count}`, `{lines_added}`, `{lines_removed}`: Diff statistics
- `{staged_diff}`: Output of `git diff --cached` (possibly truncated)

### Optional Sections

If a field is empty, omit the entire section:

```python
if repository_instructions:
    prompt += f"\nRepository instructions:\n{repository_instructions}\n"
else:
    # Omit section entirely
    pass
```

## Format-Specific Task Prompts

### Freeform Format (Default)

```
Generate a commit message in natural language.

Requirements:
- Use imperative mood (e.g., "Add feature" not "Added feature")
- Keep it concise (1-3 sentences)
- Focus on the most significant changes
- No special formatting required

Output only the commit message text, nothing else.
```

### Conventional Commits Format

```
Generate a commit message following Conventional Commits specification.

Format: type(scope): description

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation changes
- style: Code style/formatting (no logic change)
- refactor: Code restructuring (no behavior change)
- test: Adding or updating tests
- chore: Build process, dependencies, etc.

Requirements:
- type is REQUIRED
- scope is OPTIONAL (use if changes are focused on one area)
- description must be lowercase, imperative mood
- Keep total length under 100 characters
- No period at end of description

Examples:
feat(auth): add JWT token validation
fix(api): handle null pointer in user endpoint
docs: update installation instructions

Output only the commit message (one line), nothing else.
```

### Gitmoji Format

```
Generate a commit message with a relevant emoji prefix (gitmoji style).

Common emojis and their meanings:
✨ :sparkles: - New feature
🐛 :bug: - Bug fix
📝 :memo: - Documentation
💄 :lipstick: - UI/styling
♻️ :recycle: - Refactoring
✅ :white_check_mark: - Tests
🔧 :wrench: - Configuration
⚡ :zap: - Performance
🔒 :lock: - Security

Format: emoji description

Requirements:
- Choose emoji based on primary change type
- Description should be concise, imperative mood
- Use only ONE emoji (the most relevant)

Examples:
✨ Add JWT authentication
🐛 Fix null pointer in user endpoint
📝 Update installation guide

Output only the commit message (emoji + description), nothing else.
```

## Token Budget Allocation

Target total: 8000 tokens  
Breakdown:
- System prompt: ~200 tokens
- Task prompt: ~200-400 tokens (varies by format)
- Context metadata: ~200 tokens
- Commit history: ~500 tokens (5 commits × ~100 tokens each)
- Repository instructions: ~200 tokens
- Learning examples: ~500 tokens (5 examples × ~100 tokens each)
- Staged diff: ~6000 tokens (remaining budget)

### Truncation Strategy

If staged diff exceeds budget:

1. **Preserve** (always keep):
   - File headers (`+++`/`---` lines)
   - Function/class signatures
   - First 10 lines of each function body

2. **Truncate** (remove if needed):
   - Large repeated patterns (minified code, auto-generated files)
   - Function bodies beyond first 10 lines
   - Test fixtures with >100 lines

3. **Summary** (add if truncated):
   ```
   [Diff truncated - showing key changes only]
   Total: {total_files} files, {total_lines} lines changed
   ```

4. **Warning** (show to user):
   ```
   Warning: Large diff truncated to fit token limits.
   Consider splitting this commit into smaller logical changes.
   ```

## Learning Examples Format

When learning is enabled and history exists:

```
Previous style examples from this repository:

Example 1:
Generated: "Add authentication"
You edited to: "feat(auth): implement JWT-based authentication"

Example 2:
Generated: "Fix bug in API"
You edited to: "fix(api): handle null pointer in user endpoint"

Example 3:
Generated: "Update docs"
You edited to: "docs: add troubleshooting section to README"

Please match this editing style in your response.
```

## Error Handling in Prompts

If context extraction fails, use degraded prompts:

### No Commit History Available (First Commit)

Omit history section, add note:
```
Note: This appears to be the first commit in this repository.
No commit history available for style reference.
```

### Binary Files in Diff

Replace binary sections:
```
File: image.png
[Binary file - content not shown]
```

Add guidance:
```
Note: Some files are binary. Mention them by name if significant.
```

### Empty or Minimal Changes

If diff is very small (<10 lines):
```
Note: This is a small change. Be especially concise.
```

## Prompt Assembly Algorithm

```python
def build_prompt(
    staged_diff: str,
    format: str,
    commit_history: list[str],
    repo_instructions: str | None,
    user_hint: str | None,
    learning_examples: list[tuple[str, str]] | None,
) -> str:
    # 1. Start with system prompt
    prompt = BASE_SYSTEM_PROMPT
    
    # 2. Add context
    prompt += build_context(
        staged_diff=staged_diff,
        commit_history=commit_history,
        repo_instructions=repo_instructions,
        user_hint=user_hint,
        learning_examples=learning_examples,
    )
    
    # 3. Add format-specific task
    prompt += get_task_prompt(format)
    
    # 4. Check token count
    token_count = estimate_tokens(prompt)
    if token_count > MAX_TOKENS:
        prompt = truncate_diff(prompt, target_tokens=MAX_TOKENS)
    
    return prompt
```

## Testing Prompts

Each prompt template should be tested with:

1. **Minimal input**: Single-file, small diff
2. **Typical input**: 3-5 files, ~200 lines changed
3. **Large input**: 10+ files, >1000 lines changed (test truncation)
4. **Edge cases**: Binary files, empty commits, no history
5. **Learning context**: With and without few-shot examples

## Validation

Generated messages must be validated:

```python
def validate_message(message: str, format: str) -> bool:
    # Basic checks
    if not message or len(message) > 1000:
        return False
    
    # Format-specific validation
    if format == "conventional":
        return bool(re.match(r'^(feat|fix|docs|style|refactor|test|chore)(\(.+\))?: .+', message))
    elif format == "gitmoji":
        return bool(re.match(r'^[\U0001F300-\U0001F9FF] .+', message))
    else:  # freeform
        return True
```

## Prompt Versioning

Track prompt template versions for reproducibility:

```python
PROMPT_VERSION = "1.0.0"
# Stored in learning records for debugging
```

Future versions may adjust templates based on:
- LLM model improvements
- User feedback on message quality
- New commit message conventions
