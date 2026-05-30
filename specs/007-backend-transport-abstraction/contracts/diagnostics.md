````markdown
# Contract: Backend Resolution Diagnostics

## Goal

Make the resolved execution context visible to users without exposing backend-specific controls that are not yet active.

## Diagnostic surfaces in scope

- `gmuse info`
- generation-time validation and error messages
- documentation examples and troubleshooting guidance

## Required diagnostic content

When resolution succeeds, diagnostics MUST be able to show:

- resolved backend
- resolved model
- resolution source or reason (for example: explicit backend, native backend hint, single configured backend)

When a later backend feature introduces active backend-specific settings, diagnostics MUST also show those active settings.

## Initial-release limitation

- The initial direct-backend implementation MUST NOT advertise concrete backend-specific advanced settings as currently usable user options.
- Diagnostics MAY omit a backend-settings section entirely when no backend-specific settings are active.

## Error content requirements

Error output for backend resolution MUST explain both:

- why resolution failed
- how the user can recover

Examples of recovery guidance:

- specify `--backend`
- set `GMUSE_BACKEND`
- configure a compatible model
- add the missing backend credentials

## Terminology contract

- Use `backend` as the umbrella term for request transport selection.
- Use `provider` only when the distinction between backend and a specific direct or routed provider is materially relevant.

## Testability expectations

- Unit and integration tests may pin the presence of required diagnostic fields.
- Tests should avoid over-constraining exact prose unless the wording itself is a user-facing contract.

````
