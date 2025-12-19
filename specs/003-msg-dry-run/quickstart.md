# Quickstart: `gmuse msg --dry-run`

## Goal

Preview the exact prompts `gmuse` would send to your LLM provider **without** making any provider calls.

## Prerequisites

- You are inside a git repository
- You have staged changes (`git add <files>`)

## Usage

1. Stage changes:

   ```bash
   git add -A
   ```

2. Run dry-run:

   ```bash
   gmuse msg --dry-run
   ```

3. You will see output like:

   ```
   MODEL: none
   FORMAT: freeform
   TRUNCATED: false

   SYSTEM PROMPT:
   ...

   USER PROMPT:
   ...
   ```

## With a hint and format

```bash
gmuse msg --dry-run --hint "security fix" --format conventional
```

## Notes

- `--dry-run` never contacts providers and does not consume tokens.
- If your diff is very large, it may be truncated; the header will show `TRUNCATED: true`.
