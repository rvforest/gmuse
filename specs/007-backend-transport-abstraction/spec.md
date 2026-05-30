# Feature Specification: Backend and Transport Abstraction

**Feature Branch**: `007-backend-transport-abstraction`
**Created**: 2026-05-29
**Status**: Draft

## Clarifications

### Session 2026-05-29

- Q: What backend scope should this feature cover initially? → A: Only current built-in direct backends are in scope for this feature; intermediary backends are enabled by the abstraction but added in later specs.
- Q: How should users explicitly choose the active backend? → A: Expose backend selection consistently via CLI flag, environment variable, and config file.
- Q: What user-facing terminology should this feature standardize on? → A: Use `backend` as the umbrella term, and use `provider` only when specifically referring to a direct provider or routed upstream provider.
- Q: What should this feature do about backend-specific settings in the initial implementation? → A: Define and reserve the mechanism now, but do not add concrete user-facing backend-specific options until a later backend feature needs them.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Preserve Simple Direct Setup (Priority: P1)

As a user who connects gmuse directly to a model provider, I want backend resolution to stay simple so my existing setup keeps working without forcing me to learn transport details.

**Why this priority**: The abstraction only helps if it preserves the current low-friction path for users who are talking directly to a provider.

**Independent Test**: Configure one compatible direct backend, run message generation without explicitly selecting a backend, and confirm generation succeeds with a resolved backend and model.

**Acceptance Scenarios**:

1. **Given** one compatible direct backend is configured and the user has not selected a backend or model, **When** they generate a commit message, **Then** the system resolves that backend automatically and uses its maintained default model.
2. **Given** the user selects a model that clearly names a supported native backend and no backend has been selected explicitly, **When** they generate a commit message, **Then** the system prefers that backend automatically if it is configured and compatible.
3. **Given** no backend is selected explicitly and the chosen model does not clearly name a supported backend, **When** the user generates a commit message, **Then** the system fails with a clear error that explains how to choose a compatible backend or model.

---

### User Story 2 - Choose Backend Independently Of Model (Priority: P2)

As a user with more than one possible connection path, I want to select the backend independently of the model so I can control how gmuse reaches the model service.

**Why this priority**: The abstraction is not useful if users cannot deliberately choose between compatible backends when more than one is available.

**Independent Test**: Configure multiple compatible backends, explicitly choose one backend, and confirm the selected backend is the one used or validated before generation.

**Acceptance Scenarios**:

1. **Given** multiple compatible backends are configured, **When** the user explicitly selects a backend, **Then** the system uses that backend instead of relying on automatic heuristics.
2. **Given** the user explicitly selects a backend that cannot serve the selected model, **When** they attempt generation, **Then** the system fails before sending the request and explains the mismatch.
3. **Given** multiple compatible backends are configured and the selected model does not clearly identify one backend, **When** the user has not explicitly selected a backend, **Then** the system fails with a clear error instead of silently guessing.

---

### User Story 3 - Reserve Space For Future Backend Controls (Priority: P3)

As a user of gmuse's current direct backends, I want the new abstraction to leave room for future backend-specific controls without adding unused complexity to the common interface today.

**Why this priority**: The abstraction should be extensible, but the initial rollout should not expose advanced controls that no in-scope backend actually uses yet.

**Independent Test**: Use a current built-in direct backend and confirm message generation does not require any new backend-specific options; inspect help, config reference, and diagnostics to confirm backend-specific controls are reserved for future backend features rather than exposed as active requirements now.

**Acceptance Scenarios**:

1. **Given** the user is using one of the current built-in direct backends, **When** they generate a commit message, **Then** no backend-specific advanced option is required.
2. **Given** no in-scope backend defines advanced backend-specific controls yet, **When** the user views help text or configuration reference, **Then** the interface does not present inactive backend-specific options as currently usable settings.
3. **Given** a future backend feature later introduces backend-specific controls, **When** those controls are added, **Then** they must be scoped under the backend-specific mechanism established by this abstraction rather than unrelated global settings.

### Edge Cases

- A model identifier names a creator or ecosystem that is not itself a directly reachable backend.
- A backend is selected or resolved successfully, but it has no maintained default model and the user did not specify one.
- A backend is selected explicitly, but the required credentials for that backend are missing.
- Multiple backends are configured, and a selected model is compatible with some but not all of them.
- Backend-specific settings remain configured after the user changes the active backend.
- Diagnostic output omits the active backend or the reason a backend/model combination was rejected.

## Constitution Check (Mandatory)

- **Code Quality**: Introduces a core resolution abstraction that affects model selection, backend selection, and validation rules. Acceptance: these responsibilities remain separately testable, deterministic, and documented without changing the default direct-backend path unnecessarily.
- **Testing**: Add unit coverage for backend detection, precedence, ambiguity handling, compatibility validation, and the reserved backend-specific setting mechanism; add integration coverage for single-backend compatibility and explicit backend selection when multiple backends are configured.
- **UX**: Update CLI help, configuration reference, and diagnostic output so users can understand the difference between backend selection, model selection, and provider-specific language. Errors must tell users how to recover from ambiguous or incompatible combinations, and the initial UX must not advertise backend-specific controls that no in-scope backend supports yet.
- **Performance**: Backend resolution and validation must add only negligible overhead compared with the current direct-provider flow. The normal direct-backend path must not require an extra preflight step just to remain usable.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST distinguish between the selected model and the selected backend when resolving a generation request.
- **FR-002**: System MUST define one backend selection flow that can represent both direct-provider connections and future intermediary or routing connections.
- **FR-003**: When one compatible direct backend is configured and the user has not explicitly selected a backend, System MUST resolve that backend automatically.
- **FR-004**: When the user selects a model that clearly names a supported native backend and the user has not explicitly selected a backend, System MUST prefer that backend automatically if it is configured and compatible.
- **FR-005**: When the user explicitly selects a backend, System MUST use that backend in preference to automatic backend resolution.
- **FR-006**: When a backend is selected or resolved and the user has not explicitly selected a model, System MUST use that backend's maintained default model if one exists.
- **FR-007**: When the selected or resolved backend cannot serve the selected or resolved model, System MUST fail before request submission with a clear, actionable error.
- **FR-008**: When no explicit backend is selected and the available information does not identify exactly one compatible backend, System MUST fail with a clear error instead of silently guessing.
- **FR-009**: System MUST provide a user-facing way to select the backend independently of the model via CLI flag, environment variable, and config file.
- **FR-010**: System MUST reserve a namespaced mechanism for backend-specific settings so advanced controls can be introduced for a backend without becoming unrelated top-level settings for all users.
- **FR-011**: The initial implementation of this feature MUST NOT require or advertise concrete backend-specific advanced options for the current built-in direct backends.
- **FR-012**: System MUST surface the resolved execution context in user-visible diagnostic output, including the active backend, resolved model, and any active backend-specific settings when a later backend feature defines them.
- **FR-013**: System MUST preserve current behavior for users whose existing configuration already resolves to a single compatible direct backend.
- **FR-014**: System MUST apply one documented resolution order across supported backends: explicit backend selection first, native backend hint second, single compatible configured backend third, and a clear error when no unique compatible backend remains.
- **FR-015**: Initial implementation of this feature MUST support the current built-in direct backends only; intermediary backends and proxy-style transports MUST be added in later feature specs on top of this abstraction.
- **FR-016**: Backend selection MUST follow the same precedence order as other core gmuse settings: CLI overrides environment variables, environment variables override config file values, and config file values override defaults.
- **FR-017**: User-facing documentation and diagnostics introduced by this feature MUST use `backend` as the umbrella term and reserve `provider` for cases where the distinction between backend and direct or routed provider is materially relevant.

### Key Entities *(include if feature involves data)*

- **Backend selection**: The user-visible choice, or resolved default, that determines how gmuse sends a generation request.
- **Model selection**: The user-visible choice, or resolved default, that determines which model the active backend should use.
- **Resolution context**: The computed combination of backend, model, and active backend-specific settings that will be used for one generation request.
- **Backend-specific setting namespace**: A scoped set of advanced options that apply only when a particular backend is active.
- **Provider**: A direct model service or routed upstream vendor referenced only when a more specific concept than `backend` is needed.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In automated compatibility coverage, 100% of tested single direct-backend setups that worked before this feature still resolve to a usable backend and model without requiring new user input.
- **SC-002**: In automated validation coverage, 100% of ambiguous or incompatible backend and model combinations fail before request submission with an actionable error.
- **SC-003**: In automated CLI and configuration coverage, users can explicitly select a backend independently of model choice and see the resolved backend and model in diagnostic output.
- **SC-004**: In automated multi-backend coverage, one explicit backend choice is sufficient to produce deterministic request resolution for the selected model.

## Scope Boundaries

In scope:

- Separating backend resolution from model resolution.
- Current built-in direct backends operating under the new abstraction.
- Explicit backend selection and deterministic resolution rules.
- Validation and diagnostics for backend and model compatibility.
- A reserved namespaced place for future backend-specific settings.

Out of scope:

- Adding any specific new intermediary backend, including OpenRouter.
- Exposing concrete backend-specific advanced settings for future intermediary backends.
- Defining backend-specific routing, privacy, or provider-preference controls.
- Changing prompt content or commit message formatting behavior beyond request resolution.

## Assumptions

- Existing direct provider integrations will continue to exist and will become direct backends under the new abstraction.
- Some model identifiers imply a creator or ecosystem, but model identity alone is not always sufficient to determine the correct backend.
- Future intermediary backends may expose controls that apply only when that backend is active.
- This feature establishes the abstraction needed for future backend-specific features, but does not itself add a new backend.
- The initial supported backend set is limited to the direct backends gmuse already supports today.

## Dependencies

- Existing credential detection and model resolution behavior remain available as inputs to the new backend resolution flow.
- Future backend-specific feature specs will build on this abstraction instead of redefining core backend and model resolution rules.
