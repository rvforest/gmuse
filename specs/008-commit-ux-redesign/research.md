# Phase 0 Research: commit UX redesign

## Current implementation baseline

- `gmuse` currently exposes `msg`, `info`, `auth`, `config`, `git-completions`, and `git-completions-run` from `src/gmuse/cli/main.py`.
- Raw generation already has a reusable service boundary in `gmuse.commit.gather_context()` and `gmuse.commit.generate_message()`.
- Clipboard behavior is currently mixed into the `msg` command via `--copy`, `GMUSE_COPY`, and `copy_to_clipboard`.
- Shell completion already bypasses `msg` and calls `gmuse.cli.completions.completions_run_command()` directly, which emits JSON and calls `generate_message()` without invoking CLI prompts.
- `python -m gmuse` is a thin wrapper around the same Typer app in `src/gmuse/__main__.py`, so command registration changes in `main.py` automatically apply to both entrypoints.
- The existing test suite already uses the two patterns this feature needs:
  1. unit tests with monkeypatch/mocks around CLI helpers, and
  2. integration tests with `CliRunner` plus real temporary git repositories.

## Research decisions

### 1. Git invocation strategy

#### Accept / `--yes`

Use:

```text
git commit --cleanup=verbatim --file -
```

and pass the generated draft through `subprocess.run(..., input=message, text=True)`.

Why this is the safest fit:

- avoids shell quoting problems entirely;
- preserves multiline messages without splitting subject/body across repeated `-m` flags;
- works cross-platform with normal `subprocess` argument lists;
- keeps the commit message off the process list;
- lets git still run normal hooks and validation.

#### Edit

Use:

```text
git commit --cleanup=verbatim --edit --file <tempfile>
```

where `<tempfile>` contains the generated draft and is created with standard-library temp-file APIs.

Why this is the best handoff:

- `--edit` preserves the normal git editor flow instead of inventing a custom editor UX;
- `--file` pre-fills the draft exactly once, which matches the requirement better than `--template`;
- a temp file is simpler and more portable than trying to synthesize editor state through environment tricks;
- the generated draft remains the initial message even if the user has a personal `commit.template`.

`--template` is not the preferred mechanism here because git aborts when the template is left unedited, which makes “open the editor and keep the draft mostly as-is” unnecessarily fragile.

#### Failure handling

Add thin wrappers in `src/gmuse/git.py` (or a small helper module beside it) that:

- call `subprocess.run(..., check=False, capture_output=True, text=True)`;
- treat exit code `0` as the only success path;
- surface stderr/stdout details on failure without printing a success-shaped message first;
- map failures into three user-facing buckets:
  1. **commit rejected**: hook failure, validation failure, or other git refusal;
  2. **editor launch/edit failure**: editor exits non-zero or git reports it could not launch the editor;
  3. **user-aborted/no commit created**: editor path exits without creating a commit.

For the editor path, the wrapper should compare `HEAD` before and after the command when possible. That makes “non-zero but no commit created” explicit and avoids guessing solely from stderr text.

### 2. Clipboard compatibility policy

The new command split should treat clipboard support as retired behavior, not as a first-class feature to preserve.

Recommended policy:

- `gmuse generate` stays strictly raw-output oriented and never performs clipboard work.
- `gmuse commit` also ignores clipboard settings; its job is to commit, not copy.
- `gmuse msg` remains temporarily available as a deprecated alias for raw generation.
- `gmuse msg --copy` becomes a hard migration error with clear guidance:
  - use `gmuse commit` for direct commits;
  - use `gmuse generate | <clipboard-tool>` if the user still wants a copy-based shell workflow.

For legacy config/env inputs:

- continue parsing `GMUSE_COPY` and `copy_to_clipboard` for one transition line so old config files do not crash command startup;
- treat them as inert no-ops on `generate`, `commit`, and `git-completions-run`;
- document them as deprecated and remove them from help/examples;
- reject new writes to that setting in config-management UX if the config command is updated as part of the redesign.

This balances migration guidance against the raw-command contract:

- success on `gmuse generate` still writes only the message to stdout;
- completion behavior is not destabilized by stale clipboard env/config;
- explicit clipboard requests fail loudly, but passive old settings do not silently alter the new command behavior.

### 3. Typer command and alias strategy

The cleanest Typer shape is:

- keep one undecorated helper for shared raw-generation option parsing/execution;
- expose that helper through a real `generate` command;
- expose a separate `msg` command wrapper that emits a deprecation notice to stderr, then delegates to the same helper;
- add a separate `commit` command that reuses the same generation inputs but routes into the new commit-session orchestration.

Implementation notes:

- register `commit` before `generate`/`msg` so help output presents the new primary workflow first;
- keep `git-completions-run` as its own top-level command;
- do not implement `generate` by shelling out to `msg`, or `msg` by shelling out to `generate`; both should call shared Python helpers directly;
- keep `src/gmuse/__main__.py` unchanged so `python -m gmuse` continues to invoke the same app object.

Typer does not need a special alias mechanism here. A small deprecated wrapper is clearer than trying to force one command object to carry multiple behavioral modes.

### 4. Interactive review-loop test strategy

The feature is testable with the repo’s existing pytest patterns.

#### Unit tests

Prefer a small orchestration layer in `src/gmuse/cli/commit_session.py` that depends on injectable helpers for:

- draft generation;
- prompting for the next review action;
- direct commit execution;
- editor-based commit execution.

That makes the core loop easy to test without running real git/editor processes. Unit tests should cover:

- first-draft accept;
- regenerate followed by accept;
- regenerate followed by abort;
- edit success;
- edit failure;
- non-interactive guard behavior;
- deprecated alias messaging;
- clipboard migration errors.

For interactive CLI tests, `CliRunner.invoke(..., input=...)` is sufficient for menu-driven review flows. Regenerate loops can be tested by making the mock generator return a sequence of drafts.

#### Integration tests

Use the existing temporary git repository pattern from `tests/integration/test_cli.py`.

Recommended integration techniques:

- **accept / `--yes`**: run against a real repo, then inspect `git log -1 --pretty=%B`;
- **abort**: verify `git rev-list --count HEAD` is unchanged;
- **regenerate**: mock the generator with sequential messages and verify the committed message is the later draft;
- **edit success**: set `GIT_EDITOR` to a tiny Python script in the temp directory that rewrites the commit message file and exits `0`;
- **edit failure**: set `GIT_EDITOR` to a script that exits non-zero;
- **non-interactive guard**: invoke in a non-TTY context and assert the command exits quickly with migration guidance.

Using a Python script for `GIT_EDITOR` is more portable than shell snippets and works across Linux, macOS, and Windows test environments.

### 5. Completion/runtime contract

The completion helper must stay on the raw generation path.

Recommended invariant:

- `gmuse git-completions-run` must continue to gather context and call `generate_message()` directly, or call a shared raw-generation helper that does the same thing;
- it must never import or invoke the interactive commit-session review loop;
- it must keep emitting JSON on stdout with the existing status contract.

Implementation guidance:

- if command code is refactored, extract a shared raw-generation helper that returns a message/result object and let both `generate` and `git-completions-run` call that helper;
- keep completion-specific timeout handling and JSON status mapping inside `src/gmuse/cli/completions.py`;
- keep the existing stderr-suppression behavior for completion runs so debug logs do not corrupt JSON output.

Regression coverage should assert that completion execution still:

- returns JSON only;
- bypasses commit prompts and editor launch paths;
- ignores retired clipboard behavior;
- preserves timeout/offline/no-staged-changes status mapping.

## Phase 1 implications

The next phase should encode these decisions into:

- a commit-session data model with explicit outcomes (`committed`, `aborted`, `failed`);
- a CLI contract that distinguishes `commit`, `generate`, and deprecated `msg`;
- a completion contract that documents the preserved raw path;
- a quickstart that treats clipboard behavior as migration-only, not as a supported destination UX.
