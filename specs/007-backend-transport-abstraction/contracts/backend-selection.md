````markdown
# Contract: Backend Selection

## Goal

Provide one deterministic contract for selecting the active backend independently of the model while preserving today's simple direct-backend path.

## User-facing selection surfaces

- CLI flag: `gmuse msg --backend <backend-name>`
- Environment variable: `GMUSE_BACKEND`
- Config file key: `backend = "<backend-name>"`

## Initial supported backend values

- `openai`
- `anthropic`
- `cohere`
- `azure`
- `gemini`

## Configuration precedence

Backend selection follows the same precedence as other core gmuse settings:

1. CLI flag
2. Environment variable
3. Config file
4. Default (`null` / no explicit backend)

## Resolution order

If the user explicitly selected a backend through any configuration surface, that backend MUST be used in preference to automatic backend resolution.

If no explicit backend is selected, the system MUST resolve in this order:

1. A selected model that clearly names a configured compatible native backend
2. Exactly one configured compatible built-in direct backend
3. Otherwise, fail with an actionable ambiguity error

## Compatibility rules

- An explicit backend MUST be validated against the selected model before request submission.
- A native backend hint derived from the selected model MUST be honored when that backend is configured and compatible, but MUST NOT be treated as proof that no other backend could serve the model.
- If an explicit backend is selected but no model is selected, the backend's maintained default model MUST be used.
- If a backend is resolved automatically and no model is selected, that backend's maintained default model MUST be used.
- If the selected or resolved backend cannot serve the selected or resolved model, the command MUST fail before request submission.

## Credential rules

- A backend selected explicitly or automatically MUST have the required credentials configured.
- If credentials are missing for the selected backend, the command MUST fail with a clear remediation hint.

## Backend-specific settings rule

- The abstraction reserves a backend-specific settings namespace.
- No concrete backend-specific advanced settings are active for the current built-in direct backends in this feature.

## Error contract

Errors MUST be actionable and distinguish at least these cases:

- no compatible backend configured
- ambiguous backend selection
- backend/model mismatch
- selected backend missing credentials

````
