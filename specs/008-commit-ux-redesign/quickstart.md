# Quickstart: commit UX redesign

This redesign makes `gmuse commit` the main workflow, keeps `gmuse generate` as the scripting primitive, and turns `gmuse msg` into a temporary deprecated alias.

## 1. Review and commit interactively

```bash
gmuse commit
```

Expected behavior:

- `gmuse` generates a draft from staged changes.
- The draft is shown before any commit is created.
- You can accept, edit, regenerate, or abort.

Use this when you want `gmuse` to replace the old “generate, copy, then run `git commit`” workflow.

## 2. Commit immediately when you trust the first draft

```bash
gmuse commit --yes
```

Expected behavior:

- `gmuse` generates one draft.
- It immediately runs `git commit` with that message.
- No review prompt or editor is opened.

Use this for the fastest explicit one-command path.

## 3. Generate a raw message for scripts or pipes

```bash
gmuse generate
```

Expected behavior:

- stdout contains only the generated commit message.
- No commit is created.
- No editor or review UI appears.

That makes `gmuse generate` the supported replacement for scripts that previously consumed `gmuse msg`.

## 4. Keep using the old command during the transition

```bash
gmuse msg
```

Expected behavior:

- stdout behaves like `gmuse generate`.
- stderr shows a deprecation notice telling you to migrate.

Use this only as a short-term compatibility path while updating habits and scripts.

## 5. Migrate old clipboard workflows

Old workflow:

```bash
gmuse msg --copy
```

New supported options:

```bash
gmuse commit
```

or, if you still want a shell clipboard pipeline:

```bash
gmuse generate | pbcopy
```

Expected behavior:

- `gmuse msg --copy` now fails with migration guidance.
- `gmuse commit` is the direct replacement for “generate then commit”.
- `gmuse generate | <clipboard-tool>` is the replacement for personal copy-based shell workflows.

## 6. Non-interactive environments must choose explicitly

If you are in a non-interactive environment:

```bash
gmuse commit
```

must fail fast with guidance to use:

```bash
gmuse commit --yes
```

or:

```bash
gmuse generate
```

This prevents hidden hangs waiting for prompt input.

## 7. Shell completions stay on the raw path

```bash
gmuse git-completions-run --shell zsh --for "git commit -m"
```

Expected behavior:

- completion still returns JSON only;
- completion still uses raw generation;
- completion never opens the interactive commit flow.
