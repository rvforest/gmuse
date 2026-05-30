````markdown
# Data Model: Backend and Transport Abstraction

## Entity: `BackendDefinition`

**Meaning**: A static description of one supported backend in the initial abstraction.

**Fields**:

- `name`: stable backend identifier (`openai`, `anthropic`, `cohere`, `azure`, `gemini`)
- `kind`: backend category; initial value set is `direct`
- `credential_signals`: one or more environment variables that indicate the backend is configured
- `default_model`: maintained default model used when the backend is active and no explicit model is supplied
- `model_compatibility_rule`: logic that determines whether a selected model can be served by this backend
- `backend_settings_namespace`: reserved namespace for future backend-specific settings; initially empty for all in-scope backends

**Validation**:

- `name` MUST be unique across supported backends.
- Every in-scope backend MUST define at least one credential signal.
- Every in-scope backend MUST define a maintained default model for the auto-resolution path.

## Entity: `BackendSelection`

**Meaning**: The user-visible backend choice, or computed backend result, for a generation request.

**Fields**:

- `value`: backend name or `null`
- `source`: one of `cli`, `environment`, `config_file`, `native_backend_hint`, `single_configured_backend`, or `unresolved`
- `status`: one of `resolved`, `ambiguous`, `invalid`, or `missing_credentials`
- `reason`: human-readable explanation used in diagnostics or errors

**State transitions**:

- `unresolved` → `resolved`: a unique compatible backend is identified
- `unresolved` → `ambiguous`: more than one compatible backend remains without an explicit selection
- `resolved` → `invalid`: backend is incompatible with the selected model
- `resolved` → `missing_credentials`: backend was selected explicitly but required credentials are absent

## Entity: `ModelSelection`

**Meaning**: The model choice, or computed default model, for a generation request.

**Fields**:

- `value`: explicit or resolved model identifier
- `source`: one of `cli`, `environment`, `config_file`, `backend_default`, or `unresolved`
- `native_backend_hint`: optional backend identifier derived from the model name when it clearly maps to a native backend

**Validation**:

- If `source` is `backend_default`, the active backend MUST provide a maintained default model.
- If `native_backend_hint` is present, it may guide backend resolution but MUST NOT override an explicit backend selection or be treated as a unique selector when multiple compatible backends exist.

## Entity: `ResolutionContext`

**Meaning**: The fully resolved execution context used for one generation request.

**Fields**:

- `backend`: resolved `BackendSelection`
- `model`: resolved `ModelSelection`
- `backend_settings`: reserved mapping of backend-specific settings, initially empty for in-scope backends
- `diagnostic_source`: short description of why the backend/model combination was chosen

**Relationships**:

- `ResolutionContext.backend` MUST be resolved before request submission.
- `ResolutionContext.model` MUST be compatible with `ResolutionContext.backend`.
- `ResolutionContext.backend_settings` MAY be empty; for this initial feature, it is expected to be empty for all supported direct backends.

## Entity: `BackendSettingsNamespace`

**Meaning**: A scoped namespace reserved for advanced settings that apply only when a specific backend is active.

**Initial behavior**:

- Present as an extension point in the abstraction.
- No concrete advanced settings are defined for the current built-in direct backends.

**Transition rule**:

- A later backend feature may populate this namespace for a specific backend, but only under the reserved backend-specific mechanism established here.

````
