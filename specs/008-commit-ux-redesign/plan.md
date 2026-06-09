# Implementation Plan: Breaking CLI UX Redesign for Commit Message Generation

**Branch**: `008-commit-ux-redesign` | **Date**: 2026-06-06 | **Spec**: ../008-commit-ux-redesign/spec.md
**Input**: Feature specification from `specs/008-commit-ux-redesign/spec.md`


## Summary

Promote `gmuse commit` to the primary user workflow by splitting today's `gmuse msg`
behavior into two explicit layers:

1. a raw stdout-only generation primitive exposed as `gmuse generate` (with
   `gmuse msg` kept temporarily as a deprecated alias), and
2. a new commit-session workflow exposed as `gmuse commit` that generates a draft,
   lets the user accept/edit/regenerate/abort, and then executes `git commit`
   directly.

The implementation should keep `gmuse.commit.generate_message` and the existing
completion runtime helper as the shared non-interactive generation path, while
moving commit orchestration, editor handoff, non-interactive guards, and migration
messaging into focused CLI helpers. Clipboard-first behavior becomes a migration
case rather than a supported workflow.

## Technical Context

**Language/Version**: Python 3.10+

**Primary Dependencies**: Typer CLI, existing gmuse prompt/generation stack
(`gmuse.commit`, LiteLLM-backed `gmuse.llm`), standard library (`subprocess`,
`os`, `sys`), pytest, Ruff, pyrefly

**Storage**: Existing filesystem/git repository state plus current env/config
inputs; no new persistent storage

**Testing**: pytest unit + integration tests, with mocked LLM/generic git command
execution for CLI review flows and real temporary git repositories for end-to-end
behavior

**Target Platform**: Local Python CLI on Linux, macOS, and Windows in both
interactive terminals and non-interactive/scripted environments

**Project Type**: Single Python package (`src/gmuse`) with a Typer-based CLI
entrypoint

**Performance Goals**: Preserve current single-generation latency for
`gmuse generate` and `gmuse commit --yes`; keep default interactive review to one
generation per draft unless the user explicitly regenerates; preserve completion
runtime behavior through the existing raw generation/helper path

**Constraints**: `gmuse generate` stdout must remain message-only on success;
`gmuse commit` must never hang in non-interactive environments without `--yes`;
completion support must continue through `gmuse git-completions-run` rather than
the interactive command; existing message-shaping options must remain available;
breaking rename/removal behavior must ship with explicit migration guidance

**Scale/Scope**: Cross-cutting CLI redesign touching command registration, git
execution, deprecated clipboard/config handling, completion/runtime contracts,
documentation, and acceptance/integration coverage

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution gates for this feature:

- **Code Quality Gate**: Pass. The redesign can stay modular by keeping raw
  generation in existing service code and introducing a small commit-session
  helper/module rather than embedding review-loop and git-commit subprocess logic
  directly into `src/gmuse/cli/main.py`.
- **Testing Gate**: Pass. The plan includes unit coverage for command wiring,
  migration errors, and review-loop branching plus integration coverage for
  interactive/non-interactive commit flows, deprecated aliases, and completion
  behavior.
- **UX Gate**: Pass. This is a breaking CLI change, so help text, errors,
  deprecation notices, quickstart material, and configuration docs are all part of
  the implementation scope.
- **Performance Gate**: Pass. The shared raw generation path is retained, no extra
  provider calls are added on accept/abort flows, and completion plumbing remains
  decoupled from interactive prompts and editor launch behavior.
- **Security/Privacy Gate**: Pass. The redesign does not add new secret storage;
  it preserves existing credential resolution, keeps completion output structured,
  and avoids leaking generated drafts or credential state through unexpected prompt
  flows.
- **Release Discipline Gate**: Pass. The plan explicitly includes a transitional
  `gmuse msg` alias, migration messaging for retired clipboard behavior, and docs
  updates appropriate for a pre-1.0 breaking change.

Checklist:

- Code Quality Gate: Yes — add a focused commit-session orchestration layer and
  keep `main.py` thin.
- Testing Gate: Yes — cover raw generation, review actions, git failures,
  deprecation messages, and completion invariants.
- UX Gate: Yes — update help, docs, migration guidance, and command descriptions.
- Performance Gate: Yes — keep completion/runtime generation on the raw helper
  path and avoid extra LLM calls unless the user asks to regenerate.
- Security/Privacy Gate: Yes — no new persistence or secret exposure paths.
- Release Discipline Gate: Yes — breaking rename/removal ships with transitional
  aliasing and documented migration.

## Project Structure

### Documentation (this feature)

```text
specs/008-commit-ux-redesign/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── cli-commands.md
│   └── completion-runtime.md
└── tasks.md
```

### Source Code (repository root)

```text
src/gmuse/
├── cli/
│   ├── main.py                # command registration, renamed surfaces, help text
│   ├── completions.py         # preserve raw completion/runtime-helper contract
│   ├── config_resolution.py   # shared option/config resolution if command plumbing changes
│   └── commit_session.py      # new interactive review + direct commit orchestration
├── commit.py                  # shared raw draft generation service remains the primitive
├── config.py                  # retire/deprecate clipboard-centric config/env handling
├── exceptions.py              # non-interactive/migration/git-commit UX errors as needed
└── git.py                     # add commit execution/editor handoff helpers around git

tests/
├── integration/
│   ├── test_cli.py
│   ├── test_cli_generate_commit.py
│   └── test_completions_run.py
└── unit/
    ├── test_cli_main.py
    ├── test_cli_completions.py
    ├── test_cli_commit_session.py
    ├── test_commit.py
    └── test_config.py

docs/source/
├── reference/
│   ├── cli.md
│   └── configuration.md
├── tutorials/
│   └── quickstart.md
├── how_to/
│   ├── completions.md
│   ├── configuration.md
│   └── troubleshooting.md
├── explanation/
│   └── how_it_works.md
└── development/
    └── shell-completions.md

README.md
```

**Structure Decision**: Keep the existing single-package CLI structure. Introduce
one small orchestration module for the interactive commit session and extend the
existing git/config/CLI modules around it, while preserving `gmuse.commit` and
`gmuse.cli.completions` as the shared raw generation path used by scripts and
completion helpers.

## Complexity Tracking

No constitution violations are expected for this feature.

## Phase 0 — Outline & Research (Output: `research.md`)

Research focus areas:

- Determine the safest cross-platform git invocation for:
  - accepting a reviewed draft immediately,
  - opening the user's normal git editor flow with a generated draft prefilled, and
  - surfacing hook/editor failures without creating false-success UX.
- Define the compatibility policy for legacy clipboard inputs (`--copy`,
  `GMUSE_COPY`, and `copy_to_clipboard`) so the new raw command remains
  stdout-only while users still get actionable migration guidance.
- Confirm the Typer command/alias strategy for making `gmuse commit` primary,
  introducing `gmuse generate`, and keeping `gmuse msg` as a temporary deprecated
  alias without disturbing `python -m gmuse` entrypoint behavior.
- Confirm test techniques for the interactive review loop, especially regenerate
  cycles and editor/abort outcomes in automated tests.
- Re-verify the completion contract so `gmuse git-completions-run` continues to
  call the shared raw generation path and never enters interactive commit logic.

Output artifact:

- `specs/008-commit-ux-redesign/research.md`

## Phase 1 — Design & Contracts (Outputs: `data-model.md`, `contracts/`, `quickstart.md`)

Design artifacts:

- Session/data model for drafts, review actions, commit outcomes, and migration
  notices: `specs/008-commit-ux-redesign/data-model.md`
- CLI surface contract covering `commit`, `generate`, deprecated `msg`, and
  retired clipboard inputs: `specs/008-commit-ux-redesign/contracts/cli-commands.md`
- Completion/runtime contract documenting the preserved raw helper path:
  `specs/008-commit-ux-redesign/contracts/completion-runtime.md`
- User migration walkthrough and examples:
  `specs/008-commit-ux-redesign/quickstart.md`

Phase 1 agent context update:

- Update `.github/copilot-instructions.md` so the Speckit plan reference points to
  `specs/008-commit-ux-redesign/plan.md`.

Post-design constitution re-check:

- Code Quality: keep raw generation and commit-session orchestration separate.
- Testing: verify both review-loop branches and raw generation/alias behavior.
- UX: confirm help output, migration text, and docs all present `commit` as the
  main workflow.
- Performance: completion/runtime helper still bypasses interactive logic.
- Security/Privacy: no new credential or draft leakage through prompts/logging.
- Release Discipline: transitional alias and retired clipboard guidance are fully
  documented before implementation starts.

## Phase 2 — Implementation Planning (Tasks breakdown; `tasks.md` created by `/speckit.tasks`)

Planned implementation steps:

1. Extract the current `gmuse msg` generation flow in `src/gmuse/cli/main.py`
   into a shared raw-generation command helper that gathers context, preserves the
   current message-shaping flags, warns on truncation, and prints only the
   generated message to stdout on success.
2. Add a new top-level `gmuse generate` command that uses that helper as the
   supported scripting/completion primitive and carries forward existing generation
   options such as `--hint`, `--format`, `--model`, `--history-depth`,
   `--temperature`, `--max-tokens`, `--max-diff-bytes`, `--include-branch`, and
   prompt-inspection/debug options that still belong on the raw path.
3. Convert `gmuse msg` into a temporary deprecated alias for `gmuse generate`,
   emitting deprecation guidance on stderr while preserving stdout compatibility
   for scripts that still consume the generated message.
4. Add a new `gmuse commit` command that reuses the shared generation inputs,
   defaults to an interactive review flow when stdin/stdout are TTYs, and supports
   `--yes` as the explicit non-interactive fast path.
5. Implement a dedicated commit-session helper (`src/gmuse/cli/commit_session.py`)
   that manages review state and actions:
   - accept → create the git commit from the current draft,
   - edit → hand off to the user's normal git authoring/editor flow with the draft
     prefilled,
   - regenerate → request a fresh draft through the shared raw generation service,
   - abort → exit without creating a commit.
6. Extend `src/gmuse/git.py` (or the new session helper) with thin wrappers for
   direct commit execution and editor handoff so git hook failures, editor launch
   failures, and empty-message exits are surfaced consistently and testably.
7. Add an explicit non-interactive guard so `gmuse commit` without `--yes` fails
   fast outside an interactive terminal with guidance to use `gmuse commit --yes`
   or `gmuse generate`.
8. Retire clipboard-first behavior from the primary CLI surface:
   - remove `--copy` from `commit`/`generate` help,
   - stop honoring clipboard behavior on the new primary/raw commands,
   - make legacy clipboard usage through `gmuse msg --copy` fail with migration
     guidance,
   - deprecate or reject `GMUSE_COPY` / `copy_to_clipboard` in a way that does not
     violate the raw stdout-only contract.
9. Keep `src/gmuse/cli/completions.py` on the raw generation/runtime-helper path,
   reusing shared generation helpers where helpful, while explicitly avoiding any
   dependency on the interactive commit session.
10. Update command descriptions, top-level help text, README, CLI reference,
    quickstart, configuration docs, troubleshooting guides, and completion docs so
    `gmuse commit` is clearly primary, `gmuse generate` is clearly the primitive,
    and the `gmuse msg`/clipboard migration story is easy to follow.
11. Add unit tests for command registration/help ordering, deprecated alias
    messaging, non-interactive guard behavior, commit-session branching,
    clipboard-migration failures, and unchanged raw generation option plumbing.
12. Add integration tests covering:
    - `gmuse commit` accept, edit, regenerate, abort, and `--yes`,
    - failure paths for no staged changes, git commit rejection, and editor issues,
    - `gmuse generate` stdout-only behavior,
    - `gmuse msg` deprecation behavior and `msg --copy` migration errors,
    - unchanged JSON-based completion behavior via `gmuse git-completions-run`.
