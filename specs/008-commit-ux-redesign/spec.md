# Feature Specification: Breaking CLI UX Redesign for Commit Message Generation

**Feature Branch**: `008-commit-ux-redesign`
**Created**: 2026-06-06
**Status**: Draft
**Input**: User description: "Create a new feature spec in this repository for a breaking CLI UX redesign around commit message generation."

---

## Clarifications & Migration Decisions

- **Primary workflow**: `gmuse commit` becomes the primary, documented way to generate a message and immediately use it for a git commit.
- **Raw generation primitive**: `gmuse generate` becomes the stdout-only command for scripts, shell integration, and completion plumbing.
- **Interactive default**: `gmuse commit` defaults to an interactive review flow so users can inspect the generated message before a commit is finalized.
- **Edit-first path**: `gmuse commit --edit` generates one draft, immediately opens the user's normal commit editor with that draft prefilled, and commits after the editor exits.
- **Fast path**: `gmuse commit --yes` skips the interactive review flow and commits immediately with the first generated draft.
- **Legacy command**: `gmuse msg` becomes a deprecated compatibility alias for `gmuse generate` for one transitional release line after this redesign ships. During that period it must emit actionable migration guidance. Removal before 1.0 is allowed after that transition.
- **Clipboard direction**: Clipboard support is no longer part of the primary product UX. New command surfaces do not center or require clipboard behavior.
- **`--copy` fate**: `--copy` is removed from the primary workflow. If users invoke `gmuse msg --copy` during the transition period, the command must fail with a clear migration message pointing users to `gmuse commit` for direct commits or `gmuse generate` plus their own shell clipboard tooling if they still want copy-based workflows.
- **Completion contract**: Shell completion behavior must continue to rely on a raw generation path or dedicated runtime helper, never on the interactive commit flow.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Review and finalize an AI-generated commit interactively (Priority: P1)

As a developer with staged changes, I want `gmuse` to guide me through reviewing a generated commit message and then committing with it so I no longer need to copy text out of the terminal into a separate `git commit` step.

**Why this priority**: This is the core UX change. The redesign only succeeds if the main flow removes copy/paste friction and makes review part of the commit process.

**Independent Test**: With staged changes in a git repository, run `gmuse commit` in an interactive terminal and verify the user can see the generated draft, choose from review actions, and complete or cancel the commit without manually copying the message.

**Acceptance Scenarios**:

1. **Given** staged changes and an interactive terminal, **When** the user runs `gmuse commit`, **Then** the command generates a draft commit message, shows it for review, and presents accept, edit, regenerate, and abort choices before any commit is finalized.
2. **Given** a reviewed draft, **When** the user chooses accept, **Then** the system creates the git commit using that reviewed message and reports success.
3. **Given** a reviewed draft, **When** the user chooses edit, **Then** the system opens the user's normal commit authoring flow with the generated draft prefilled so the user can revise it before finalizing.
4. **Given** a reviewed draft, **When** the user chooses regenerate, **Then** the system replaces the current draft with a newly generated draft and returns to the same review step.
5. **Given** a reviewed draft, **When** the user chooses abort, **Then** no git commit is created and the command exits clearly without ambiguity about the outcome.

---

### User Story 2 - Commit immediately when I trust the generated draft (Priority: P1)

As a developer who wants the fastest possible flow, I want a non-interactive confirmation flag so I can generate and commit in one step when I do not need manual review.

**Why this priority**: The redesign should make the main UX better without removing an efficient path for experienced users and automation-friendly personal workflows.

**Independent Test**: With staged changes in a git repository, run `gmuse commit --yes` and verify the command creates a commit directly from the first generated draft without prompting for review.

**Acceptance Scenarios**:

1. **Given** staged changes, **When** the user runs `gmuse commit --yes`, **Then** the system generates a draft and immediately creates the git commit with that message without prompting.
2. **Given** a non-interactive environment, **When** the user runs `gmuse commit --yes`, **Then** the command can still complete successfully because it does not require an interactive prompt or editor.

---

### User Story 3 - Edit the generated draft immediately (Priority: P1)

As a developer who usually wants to polish generated messages in my normal editor, I want a flag that skips the review prompt and opens the generated draft for editing immediately.

**Why this priority**: This preserves user control while reducing steps for developers who consistently prefer editor-based commit authoring over menu-based review.

**Independent Test**: With staged changes in a git repository and a working commit editor, run `gmuse commit --edit` and verify the command generates one draft, opens the editor with that draft prefilled, and creates or aborts the commit according to the edited message.

**Acceptance Scenarios**:

1. **Given** staged changes and an interactive terminal, **When** the user runs `gmuse commit --edit`, **Then** the system generates a draft and opens the user's normal commit authoring flow immediately without showing the review action prompt.
2. **Given** the editor opens with the generated draft, **When** the user saves a usable message and exits, **Then** the system creates the git commit with the edited message.
3. **Given** the editor opens with the generated draft, **When** the user exits with no usable commit message, **Then** no git commit is created and the command reports that the commit was aborted.
4. **Given** the user runs `gmuse commit --edit --yes`, **When** the command validates the request, **Then** it fails with a usage error because edit-first and commit-immediately are conflicting modes.

---

### User Story 4 - Use raw generation for scripts and shell completion plumbing (Priority: P1)

As a developer or tool author, I want a raw stdout-only command so scripting, shell completions, and other integrations can keep using generated commit text without triggering an interactive commit workflow.

**Why this priority**: The redesign must preserve automation and completion support while separating message generation from the act of committing.

**Independent Test**: Run `gmuse generate` in a repository with staged changes and verify the command outputs only the generated commit message to stdout, with no review prompts, clipboard handling, or git commit side effects.

**Acceptance Scenarios**:

1. **Given** staged changes, **When** the user runs `gmuse generate`, **Then** the command writes only the generated commit message to stdout and exits successfully without creating a commit.
2. **Given** an existing shell completion integration, **When** completion requests a generated message, **Then** it continues to use a raw generation path or runtime helper and never triggers the interactive `gmuse commit` UX.
3. **Given** a scripted workflow that pipes output from `gmuse generate`, **When** the command succeeds, **Then** the stdout stream contains only the commit message content needed by the script.

---

### User Story 5 - Understand and migrate from the old command surface (Priority: P2)

As an existing `gmuse` user, I want the renamed commands, deprecated aliases, and removed clipboard-centric behavior to be explained clearly so I can update my habits and scripts without confusion.

**Why this priority**: This redesign is intentionally breaking. Discoverability and migration guidance are required to prevent avoidable frustration.

**Independent Test**: Run help commands and legacy commands (`gmuse msg`, `gmuse msg --copy`) and verify the user is told what changed, what replacement command to use, and whether compatibility is temporary.

**Acceptance Scenarios**:

1. **Given** the redesign has shipped, **When** the user runs `gmuse --help` or relevant subcommand help, **Then** `gmuse commit` is presented as the primary workflow and `gmuse generate` as the raw primitive.
2. **Given** a user runs `gmuse msg`, **When** the compatibility alias is still within its supported transition window, **Then** the command behaves like `gmuse generate` and emits a deprecation notice with the replacement command.
3. **Given** a user runs `gmuse msg --copy`, **When** the redesign is active, **Then** the command exits with a clear migration error that explains clipboard-first behavior is retired and points to supported alternatives.

---

### Edge Cases

- Running `gmuse commit` in a non-interactive terminal without `--yes` must not hang waiting for input; it should fail with guidance to use `--yes` or `gmuse generate`.
- Running `gmuse commit --edit` in a non-interactive terminal must fail rather than launching an editor or hanging.
- Running `gmuse commit --edit --yes` must fail as an invalid combination because one mode requires editor review while the other commits immediately.
- If there are no staged changes, all affected commands must fail clearly without creating a commit or opening an editor.
- If generation succeeds but the final git commit is rejected by git hooks or other commit-time validation, the user must receive a clear failure outcome and no false success message.
- If the user selects edit but the editor cannot be opened, the command must report the problem and leave the repository uncommitted.
- If the user exits the editor without saving a usable commit message, the command must treat that as a non-commit outcome rather than silently committing an empty or unintended message.
- Multi-line commit messages must preserve subject/body structure across interactive review, editor handoff, raw stdout generation, and the fast path.
- Completion-triggered generation must never surface interactive prompts, editor launches, or clipboard-oriented behavior.
- Legacy scripts that still call `gmuse msg` during the transition must receive deterministic behavior and deterministic deprecation messaging.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The CLI MUST provide `gmuse commit` as the primary documented command for generating a commit message and using it to create a git commit.
- **FR-002**: `gmuse commit` MUST default to an interactive review flow when standard input and output are interactive.
- **FR-003**: The interactive review flow MUST show the generated draft before finalizing the commit and MUST offer accept, edit, regenerate, and abort actions.
- **FR-004**: If the user chooses accept, the system MUST create the git commit using the currently reviewed draft message.
- **FR-005**: If the user chooses edit, the system MUST hand off the generated draft to the user's normal commit authoring flow so the user can revise the final message before commit completion.
- **FR-006**: If the user chooses regenerate, the system MUST generate a replacement draft and return the user to the review step without creating a commit from the previous draft.
- **FR-007**: If the user chooses abort, the system MUST exit without creating a git commit.
- **FR-008**: The CLI MUST provide a non-interactive fast path such that `gmuse commit --yes` generates one draft and immediately uses it for the git commit without a review prompt.
- **FR-009**: The CLI MUST provide an edit-first path such that `gmuse commit --edit` generates one draft, opens the user's normal commit authoring flow with that draft prefilled, and creates the commit only after the editor exits with a usable message.
- **FR-010**: `gmuse commit --edit` and `gmuse commit --yes` MUST be mutually exclusive.
- **FR-011**: If `gmuse commit` is invoked without an interactive terminal and without `--yes`, the command MUST fail with an actionable message directing users to `gmuse commit --yes` or `gmuse generate`.
- **FR-012**: The CLI MUST provide `gmuse generate` as the raw generation command for scripting, shell integration, and completion plumbing.
- **FR-013**: `gmuse generate` MUST write only the generated commit message to stdout on success and MUST NOT open an editor, prompt for review, create a commit, or depend on clipboard behavior.
- **FR-014**: Shell/tab completion support MUST continue to work after the redesign, and completion flows MUST remain based on a raw generation path or dedicated runtime helper rather than the interactive commit command.
- **FR-015**: `gmuse msg` MUST become a deprecated compatibility alias for `gmuse generate` for one transitional release line after the redesign is introduced.
- **FR-016**: During the compatibility window, `gmuse msg` MUST emit a deprecation notice that names `gmuse generate` as the replacement for raw output use cases and `gmuse commit` as the replacement for direct commit workflows.
- **FR-017**: `--copy` MUST NOT be part of the primary `gmuse commit` or `gmuse generate` command surfaces.
- **FR-018**: If a user invokes legacy clipboard behavior such as `gmuse msg --copy`, the command MUST fail with a clear migration message explaining that clipboard-first behavior is retired and that stdout piping or the direct commit flow are the supported alternatives.
- **FR-019**: All affected commands MUST preserve existing core commit-message-shaping inputs that remain in scope for generation, including message format options and other established context inputs, unless a separate breaking change explicitly removes them.
- **FR-020**: All affected commands MUST preserve current prerequisite validation and error behavior for unsupported contexts such as not being in a git repository, having no staged changes, or lacking required generation credentials.
- **FR-021**: Help text, command descriptions, and user-facing documentation MUST present `gmuse commit` as the main workflow, `gmuse generate` as the scripting/completion primitive, and the `gmuse msg` transition policy clearly.
- **FR-022**: The redesign MUST make review possible before commit finalization in the default interactive path, while still allowing explicit alternate modes via `--edit` and `--yes`.

### Key Entities *(include if feature involves data)*

- **Generated Draft**: A proposed commit message produced from the current staged changes and relevant generation inputs. It may contain a subject line only or a subject and body.
- **Commit Session**: A single user interaction with `gmuse commit`, including draft generation, review actions, optional editing, and either successful commit completion or explicit cancellation/failure.
- **Raw Generation Output**: The stdout-only message emitted by `gmuse generate` or equivalent completion plumbing for use by scripts and shell integrations.
- **Migration Notice**: User-facing guidance emitted when a deprecated command or removed flag is used, including the supported replacement path.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In acceptance testing, at least 90% of representative users can complete a commit with `gmuse commit` in under 30 seconds without manual copy/paste between commands.
- **SC-002**: In 100% of default interactive `gmuse commit` sessions, users are given an opportunity to review the generated draft before any commit is finalized.
- **SC-003**: In 100% of successful `gmuse generate` runs, stdout contains only the generated commit message content needed by scripts and completion plumbing.
- **SC-004**: At least 95% of completion-triggered raw generation requests either return a usable suggestion or fail cleanly within the configured completion timeout, with no interactive prompt or editor launch.
- **SC-005**: In migration validation, all deprecated entry points and removed clipboard workflows produce actionable guidance that names the correct replacement command.

---

## Assumptions

- The project is still pre-1.0, so a breaking change to the primary CLI UX is acceptable if migration behavior is clearly documented.
- The redesign changes how users reach commit generation and commit execution, but it does not expand scope into staging, amend workflows, or broader git history editing.
- Users who choose the edit path have a working commit authoring environment available through their normal git/editor configuration.
- Existing shell completion behavior continues to rely on a raw generation runtime path and should remain decoupled from any interactive commit UX.
- Clipboard-specific workflows are considered optional personal shell behavior rather than a core responsibility of `gmuse`.
