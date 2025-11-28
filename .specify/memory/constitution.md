<!--
Sync Impact Report
- Version change: N/A → 1.0.0
- Modified principles: n/a (initial adoption) → Code Quality; Testing Standards; User Experience Consistency; Performance & Resource Requirements; Observability, Versioning & Release Discipline
- Added sections: Additional Constraints (Security, Privacy & Performance); Development Workflow & Quality Gates
- Removed sections: template placeholders replaced
- Templates requiring updates: ✅ /home/forest/code/gmuse/.specify/templates/plan-template.md (updated)
                           ✅ /home/forest/code/gmuse/.specify/templates/spec-template.md (updated)
                           ✅ /home/forest/code/gmuse/.specify/templates/tasks-template.md (updated)
- Follow-up TODOs: None deferred.
-->

# gmuse Constitution

## Core Principles

### I. Code Quality (NON-NEGOTIABLE)

All source code in the `gmuse` repository MUST follow high-quality standards to keep the project maintainable and secure.

- Public functions, classes, and CLI contracts MUST be fully typed and use Google-style docstrings that include usage examples and brief rationale.
- Code MUST be well-structured and modular: each feature should start as a small, testable library. Modules MUST avoid side-effects at import time.
- Projects MUST adopt automated formatting and linting: Ruff-compatible formatting plus mypy type checking. All PRs MUST pass these checks before merge.
- Changes that make the code harder to test, harder to read, or that avoid obvious abstractions MUST be accompanied by a clear justification in the PR and a plan to mitigate risk (e.g., added tests or a follow-up PR).

### II. Testing Standards (NON-NEGOTIABLE)

Tests are essential for correctness and long-term maintainability. Test-first workflows are required for critical areas.

- Unit tests MUST exist for every public function and class; integration tests MUST cover cross-component flows and important CLI behavior.
- Testing scope and organization: tests MUST be organized under `tests/` with `unit/`, `integration/`, and `contract/` directories where relevant.
- Coverage expectations: core modules SHOULD maintain at least 80% line coverage; critical feature areas (CLI, git integration, LLM provider, learning store) MUST maintain 90%+ where practical.
- CI MUST block merges on failing unit tests, failing integration tests for release branches, or unmet coverage gates; mypy errors and linting failures MUST fail CI.
- TDD is recommended for large or risky features; tests MUST be present and failing before a feature implementation PR is completed.

### III. User Experience Consistency

User-facing behavior—including CLI flags, messages and documentation—MUST be consistent, discoverable, and minimally surprising.

- CLI design MUST adhere to `git`-like conventions; `typer` MUST be used to generate consistent help, flags, and usage patterns.
- Error messages MUST be actionable and include remediation steps. CLI changes must update the help text and the corresponding docs under `docs/`.
- Default behaviors MUST be conservative (e.g., dry-run default) and opt-in behaviors must be clearly documented (e.g., `learning_enabled` defaults to false).
- UX changes that affect user workflows (e.g., changing a default flag behavior) MUST be documented in release notes and the development spec for the feature.

### IV. Performance & Resource Requirements

Performance, cost, and resource constraints MUST be considered for all features, especially those that call LLM providers or process large diffs.

- Token usage and provider request size MUST be bounded by safe defaults (e.g., token summarization for very large diffs). LLM calls MUST have conservative timeouts and retry strategies.
- For heavy operations (large diffs, hunk-level splits), provide streaming or summarized approaches to limit memory and CPU consumption.
- Performance goals for features MUST be documented in specifications (`specs/`) and validated where possible: p95 latency targets, memory limits, and API call limits.
- CI and pre-merge checks SHOULD include basic performance smoke tests for new heavy operations where feasible.

### V. Observability, Versioning & Release Discipline

Observability and predictable releases are required for long-term stability and trust.

- Structured logging, debug modes, and a `GMUSE_DEBUG` environment variable MUST be available for troubleshooting; logs MUST mask secrets.
- Semantic versioning (MAJOR.MINOR.PATCH) MUST be followed for releases. Breaking changes require a MAJOR bump and a migration plan.
- Deprecations MUST be announced at least one minor release before removal and clearly documented in CHANGELOG and migration guides.
- Runtime behavior or configuration changes MUST be accompanied by clear release notes and documentation updates.

## Additional Constraints: Security, Privacy & Data Handling

Security and privacy are foundational constraints for the project.

- The project MUST NOT store API keys or secrets in the repository. Environment-based configuration and XDG conventions MUST be used.
- Learning data (history, edits) MUST be opt-in and stored in `$XDG_DATA_HOME/gmuse/history.jsonl` by default. Users MUST explicitly enable learning via configuration.
- Learning data MUST be minimal and avoid storing raw sensitive content; provide clear instructions to redact/censor or disable data capture.
- Documentation MUST describe how to delete or export learning history and the expected data retention strategy.

## Development Workflow & Quality Gates

The repository follows a strict workflow to maintain quality and predictability.

- PRs MUST reference a spec in `specs/` or contain a new spec and associated tasks/plan. PRs MUST be targeted to a single user story where feasible.
- All PRs MUST pass the following checks before merge into protected branches:
  - Lint and format checks (`nox -s lint`)
  - Type checking (`nox -s types`)
  - Unit tests and integration tests (`nox -s test`) with coverage gates
  - Documentation build for public API or CLI changes
- Any PR that introduces public API changes or runtime behavior changes MUST update the documentation (`docs/`) and add acceptance tests for those changes.
- Critical changes (security, data handling, release behavior) MUST be reviewed by at least one maintainer; governance changes require at least two maintainer approvals.

## Governance

Amendments to this constitution follow a clear process for transparency and stability.

- To propose a change, open a PR against `.specify/memory/constitution.md` describing the change, rationale, and any migration steps or risks.
- At least one maintainer review is required for minor changes; two maintainer approvals are required for major governance changes.
- Versioning policy: update `CONSTITUTION_VERSION` according to the rules below, and set `LAST_AMENDED_DATE` to the amendment date (UTC).

Version bump rules:
- MAJOR: Breaking governance changes or removal of core principles.
- MINOR: Adding a new principle or materially expanding guidance.
- PATCH: Clarifications and non-semantic wording edits.

**Version**: 1.0.0 | **Ratified**: 2025-11-28 | **Last Amended**: 2025-11-28

