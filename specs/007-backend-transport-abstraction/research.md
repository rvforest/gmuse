````markdown
# Phase 0 Research: Backend and Transport Abstraction

## Context

Today gmuse conflates two concepts in one provider-oriented flow:

- credential detection picks a "provider"
- model resolution assumes that provider is also the transport/backend

That works for direct providers but makes future intermediary or routed backends awkward. The initial feature scope, however, is limited to today's built-in direct backends, so the abstraction must improve the internal model without making the current user experience harder.

## Decisions

### Decision 1 — Standardize on `backend` as the umbrella term

- Decision: Use `backend` as the user-facing umbrella term for how gmuse sends a request. Reserve `provider` for cases where gmuse needs to refer specifically to a direct model provider or a routed upstream provider.
- Rationale:
  - The current code and docs use `provider` for both transport selection and model ecosystem identity.
  - The feature spec explicitly separates backend from model and reserves provider for the narrower concept.
- Alternatives considered:
  - Keep `provider` as the main umbrella term.
    - Rejected because it preserves the same conceptual conflation the feature is trying to remove.
  - Replace every provider reference everywhere immediately.
    - Rejected because some places still need the more specific provider concept.

### Decision 2 — Limit initial implementation to the current built-in direct backends

- Decision: The initial abstraction will support only the current built-in direct backends: `openai`, `anthropic`, `cohere`, `azure`, and `gemini`.
- Rationale:
  - This keeps the first abstraction step small and regression-resistant.
  - The codebase already has default-model and credential heuristics for these backends.
- Alternatives considered:
  - Treat every LiteLLM-recognizable provider as in scope immediately.
    - Rejected because the current CLI, docs, tests, and default-model behavior are only explicit for the built-in direct backends.
  - Add OpenRouter as part of this feature.
    - Rejected because this spec intentionally prepares that follow-on feature rather than bundling it into the abstraction itself.

### Decision 3 — Centralize backend resolution in one explicit resolution flow

- Decision: Replace the scattered "detect provider here, resolve model there" flow with one backend-resolution path that determines the active backend before request submission.
- Rationale:
  - Current behavior is split across `detect_provider()`, `resolve_model()`, `LLMClient.__init__()`, and `gmuse info` diagnostics.
  - A single resolution flow is easier to validate, document, and test against the new precedence rules.
- Alternatives considered:
  - Keep `detect_provider()` as the primary decision point and layer more conditions on top.
    - Rejected because it would deepen the existing coupling between provider detection and model resolution.
  - Resolve the backend only inside `LLMClient`.
    - Rejected because CLI/config diagnostics and preflight validation need access to the same decision before client construction.

### Decision 4 — Use a deterministic resolution order with explicit ambiguity failures

- Decision: Resolve the backend in this order: explicit backend selection first, a native backend hint from the selected model second when that backend is configured and compatible, single compatible configured direct backend third, and an actionable error when no unique compatible backend remains.
- Rationale:
  - This matches the clarified spec and avoids silent guesses.
  - Existing users with one configured direct backend keep the current low-friction experience.
- Alternatives considered:
  - Keep a fixed provider-priority list when multiple backends are configured.
    - Rejected because that would silently choose a backend in cases where the spec now requires determinism or an error.
  - Require explicit backend selection every time.
    - Rejected because it would unnecessarily degrade the current single-backend setup.

### Decision 5 — Expose backend selection through the same config surfaces as other core settings

- Decision: Introduce backend selection consistently via CLI flag, environment variable, and config file, with the same precedence as the rest of gmuse's core configuration.
- Rationale:
  - This matches the current configuration model and the clarification decision.
  - Users already expect settings to resolve via CLI > environment > config file > defaults.
- Alternatives considered:
  - Make backend selection CLI-only.
    - Rejected because it would make backend choice feel like a second-class concept compared with model and format.
  - Make backend selection environment-only.
    - Rejected because it would not match the existing CLI/config ergonomics.

### Decision 6 — Reserve, but do not activate, backend-specific settings in the initial release

- Decision: Establish a reserved backend-specific settings namespace in the abstraction, but do not expose concrete advanced backend-specific options for the in-scope direct backends yet.
- Rationale:
  - The abstraction needs a future-safe place for features like routed-provider choice or privacy mode.
  - No current in-scope backend needs concrete advanced settings, and the clarified spec explicitly avoids surfacing unused controls now.
- Alternatives considered:
  - Ship a generic advanced-settings surface immediately.
    - Rejected because it would add user-visible complexity without solving an in-scope problem.
  - Omit the namespace entirely.
    - Rejected because later backend features would then be forced to invent global top-level settings.

### Decision 7 — Expand diagnostics around resolution context and update wording-sensitive tests

- Decision: Update diagnostics to show the resolved backend, resolved model, and why that backend was selected. Update wording-sensitive tests and docs to align with the new terminology.
- Rationale:
  - `gmuse info` currently shows only "Detected provider heuristics" and a handful of credential checks.
  - Existing tests explicitly pin current provider wording, so the migration must be deliberate.
- Alternatives considered:
  - Leave diagnostics mostly unchanged and only update internal logic.
    - Rejected because the spec requires visible backend/model resolution and the existing output would be misleading.

## Notes / Best-practice reminders

- Keep the direct-backend path local and static; the initial abstraction should not add network calls or metadata preflights.
- Treat backend/model mismatch and ambiguity as validation failures before request submission.
- Plan docs and tests together: current unit tests pin exact provider wording, especially around `gmuse info` and missing-provider errors.

````
