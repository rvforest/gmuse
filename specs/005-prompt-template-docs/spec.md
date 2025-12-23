# Feature Specification: Prompt Template Documentation Reference

**Feature Branch**: `005-prompt-template-docs`
**Created**: 2025-12-23
**Status**: Draft
**Input**: User description: "I'd like a prompt template reference in the documentation so that users can quickly see exactly what information is getting loaded into the context window when a suggestion request is sent. I'd like this page or pages to automatically keep sync with the actual template so that there is a single source of truth and there is no drift between the two."

## Clarifications

### Session 2025-12-23

- Q: Should the prompt template be treated as a stable public contract or internal implementation? → A: Treat as stable public contract within major versions; changes only in major releases with documented migration notes.
- Q: Should the documentation reference be a single unified page or multiple pages per template/mode? → A: Single unified reference page with clear section dividers for different suggestion modes.
- Q: What are the exhaustive context inputs to be documented? → A: (1) Staged changes (diff/diff-stat output) — always included; (2) Output format (freeform/conventional/gitmoji) — always included; (3) Branch context (optional branch name info) — opt-in via `--include-branch`; (4) Commit history (recent commits for style context) — always included, configurable via `history_depth`.
- Q: How should template synchronization be automated? → A: Template extraction runs as part of `uv run nox -s docs`; build fails if canonical templates cannot be read.
- Q: What test coverage strategy should be required? → A: (1) Unit tests for template extraction readability/parseability; (2) Integration test for reference-to-template sync; (3) Drift detection test verifying build failure on template mismatch.

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.

  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - Understand What Gets Sent (Priority: P1)

As a gmuse user who is considering enabling AI suggestions (or troubleshooting them), I want a documentation page that shows exactly what information can be included in a suggestion request so I can make an informed privacy and accuracy tradeoff.

**Why this priority**: This directly supports user trust, privacy expectations, and explains “what gmuse sends” without requiring users to read source code.

**Independent Test**: Can be fully tested by viewing the published documentation and verifying it lists the prompt template(s) and the full set of context inputs (including when they are included/excluded).

**Acceptance Scenarios**:

1. **Given** I am reading the documentation, **When** I open the prompt template reference page, **Then** I can see a complete list of context inputs that may be included in a suggestion request.
2. **Given** a context input is optional, **When** I read its entry, **Then** the documentation clearly states the condition that enables it and what happens when it is disabled.

---

### User Story 2 - See the Exact Template Text (Priority: P2)

As a gmuse user, I want to view the exact prompt template text used for suggestion requests so I can understand the instructions given to the model and how my change data is framed.

**Why this priority**: The template content itself is part of what gets sent to the model; seeing it reduces confusion and helps with debugging unexpected outputs.

**Independent Test**: Can be fully tested by comparing the documentation output to the canonical template source and confirming it matches exactly (byte-for-byte, ignoring unavoidable documentation formatting wrappers).

**Acceptance Scenarios**:

1. **Given** I am on the prompt template reference page, **When** I view the canonical prompt template text for a suggestion request, **Then** the text matches the canonical template source (so users are not reading a manually-copied approximation).

---

### User Story 3 - Maintain Single Source of Truth (Priority: P3)

As a maintainer, I want the documentation reference to stay automatically synchronized with the canonical prompt template(s) so the docs never drift from what gmuse actually sends.

**Why this priority**: Drift in privacy/behavior documentation creates user distrust and can lead to incorrect expectations.

**Independent Test**: Can be fully tested by changing a canonical prompt template and observing that the documentation reference updates without manually editing the documentation reference content.

**Acceptance Scenarios**:

1. **Given** a maintainer updates a canonical prompt template source, **When** the documentation is built/published, **Then** the prompt template reference content reflects that update without manual editing of the reference content.

---

[Add more user stories as needed, each with an assigned priority]

### Edge Cases

Edge cases to explicitly cover in the documentation reference:

- Conditional context (optional inputs) is clearly labeled as optional and describes the condition that enables it.
- Multiple suggestion formats or modes (if applicable) are documented separately so users can see which template applies.
- Missing or empty context inputs (e.g., no staged changes, empty commit history, missing branch info) are described, including what gmuse sends instead.
- Sanitization/redaction rules that apply to context inputs are described at a high level (what categories are removed/masked), without exposing sensitive real examples.
- If documentation generation cannot accurately reflect the current canonical template(s), the documentation build/publish step should not silently succeed.

<!--
  NOTE: The sections below are mandatory per this repository's specification template.
-->

## Constitution Check (Mandatory)

Every specification MUST explicitly address the following constitution-oriented questions and include evidence or steps:

- **Code Quality**: Does this spec change public APIs, require new libraries, or introduce patterns that need additional linting/type checks? Describe how you'll keep code readable and testable.
- **Testing**: What unit and integration tests will be added? Are there required coverage targets or new test types (contract, performance, security) that must be in CI?
- **UX**: If the spec introduces CLI or user-visible changes, include help text, error messages, and docs that will need updates.
- **Performance**: Document expected ranges for latency, memory, or token consumption, and any strategies for keeping those within acceptable bounds.

Address each item with short acceptance criteria (e.g., "Unit tests added: file path: tests/unit/test_x.py; Coverage target: 85% for new modules").

- **Code Quality**: The feature must not require users to manually duplicate template content in docs. Any new automation should have clear inputs/outputs and be easy to validate.
- **Testing**:
  - Unit tests added: `tests/unit/test_prompt_template_extraction.py` — tests for template extraction logic, readability validation, and error handling.
  - Integration tests added: `tests/integration/test_prompt_template_docs_sync.py` — tests verifying that built documentation reference matches canonical templates byte-for-byte; tests verifying docs build fails when templates are missing/invalid.
  - Coverage target: 85% for new template extraction modules. Drift detection tests MUST cover all documented context input types.
- **UX**: The documentation page(s) must be easy to find from the documentation navigation and must clearly label what is included in requests vs what stays local.
- **Performance**: Documentation generation must not noticeably slow down the normal developer workflow; it should be bounded and predictable.

## Requirements *(mandatory)*

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
-->

### Functional Requirements

- **FR-001**: Documentation MUST include a dedicated reference page (or pages) that explains what information can be included in a suggestion request.
- **FR-002**: The reference MUST enumerate each distinct context input that may be included (e.g., change/diff data, selected output format, optional branch context), and for each input MUST state when it is included/excluded.
- **FR-003**: The reference MUST present the canonical prompt template text used for suggestion requests in a **single unified reference page**, with clear section dividers if multiple suggestion modes/templates exist. The page MUST be readable and the template text MUST be copyable.
- **FR-004**: The reference MUST be automatically synchronized with the canonical template source(s) via the documentation build process. Template extraction MUST run as part of `uv run nox -s docs`, updating the reference page without manual duplication.
- **FR-005**: The documentation build process (`uv run nox -s docs`) MUST prevent silent drift: if the canonical template source(s) cannot be read or extracted, the documentation build MUST fail with a clear, actionable error message.
- **FR-006**: The reference MUST avoid leaking sensitive user data: any examples included MUST use synthetic placeholders and MUST NOT incorporate real local repository content.
- **FR-007**: The documentation navigation MUST make the reference discoverable from the main documentation index and from relevant privacy/explanation pages.
- **FR-008**: If there are multiple canonical templates for different suggestion types/modes, the reference MUST clearly distinguish them and indicate which template is used for which request.
- **FR-009**: The reference MUST state the stability expectations: the template is considered a **stable public contract within major versions** (changes only in major releases). The documentation MUST include migration notes in the CHANGELOG for any template changes in new major versions, and point users to the CHANGELOG for version-to-version differences.

### Key Entities *(include if feature involves data)*

- **Prompt Template**: The canonical text instructions used to form a suggestion request.
- **Context Input**: A named piece of information that may be inserted into or accompany a suggestion request (with inclusion rules).
  - **Staged Changes**: Diff or diff-stat output of staged git changes. Always included in requests.
  - **Output Format**: The requested message format (freeform, conventional, or gitmoji). Always included in requests.
  - **Branch Context**: Sanitized current branch name and metadata (e.g., ticket ID extraction, type prefix). Optional, opt-in via `--include-branch` CLI flag or config.
  - **Commit History**: Recent commit messages for style/tone context. Always included; depth configurable via `history_depth` parameter (default: 5 commits).
- **Documentation Reference**: The published human-readable representation of the prompt template(s) and context inputs.

## Success Criteria *(mandatory)*

<!--
  ACTION REQUIRED: Define measurable success criteria.
  These must be technology-agnostic and measurable.
-->

### Measurable Outcomes

- **SC-001**: Users can identify all context inputs included in a suggestion request by reading a single documentation reference page in under 2 minutes.
- **SC-002**: For every canonical template used for suggestion requests, there is a corresponding documentation reference output that matches the canonical template text (no manual copying).
- **SC-003**: Drift prevention is effective: attempts to publish/build docs when canonical templates and the reference output are out of sync fail with a clear, actionable error.
- **SC-004**: Documentation support burden decreases: reduce "what data does gmuse send?" clarification issues/questions by 30% over the next two minor releases (tracked via issues/discussions labels).

## Scope Boundaries

In scope:

- Documentation reference content that reflects the canonical prompt template(s) used for suggestion requests.
- Documentation describing what context inputs can be included and when.
- Automated synchronization to avoid drift.

Out of scope:

- Changing the behavior of what gmuse sends in suggestion requests.
- Adding new suggestion request fields solely for documentation purposes.

## Assumptions

- There is a clear set of canonical prompt template source(s) in the repository that represent the actual text used for suggestion requests.
- Suggestion requests have a definable set of context inputs with clear inclusion rules (including optional/opt-in inputs).

## Dependencies

- Documentation publishing/build processes must be able to access the canonical template source(s) in the repository.
