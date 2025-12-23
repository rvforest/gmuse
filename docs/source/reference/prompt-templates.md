# Prompt Template Reference

This page documents the exact canonical prompt templates and the possible context
inputs that gmuse may include in a suggestion request.

The goal is transparency: you can understand what data may be sent to your
configured LLM provider without needing to read source code.

## Context Inputs

The following context inputs may be included in requests:

```{context-inputs-table}
```

## System Prompt

The system prompt is always included:

```{prompt-template} system
```

## Output Formats

Every request includes an output format selection. The selected format controls
which formatting instructions are included in the request:

- `freeform`
- `conventional`
- `gitmoji`

### Freeform

```{prompt-template} freeform
```

### Conventional Commits

```{prompt-template} conventional
```

### Gitmoji

```{prompt-template} gitmoji
```

## Stability & Versioning

These templates are treated as a stable public contract within a major version.
If you need to track changes over time, see the canonical definitions in
`gmuse.prompts` (notably `PROMPT_VERSION`).
