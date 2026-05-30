# ADR: Backend and Transport Abstraction

- **Status**: Draft
- **Date**: 2026-05-29
- **Context**: The current gmuse flow conflates provider detection, model resolution, and request transport. That works for today's built-in direct backends, but it makes future intermediary or routed backends difficult to add without widening the current coupling.

## Decision

Introduce `backend` as the first-class transport concept and separate it from `model` resolution.

The initial implementation will:

- support only the current built-in direct backends
- preserve the existing low-friction path for users with one compatible direct backend configured
- resolve backend selection deterministically with the following precedence:
  - explicit backend selection
   - native backend hint from the selected model
  - single compatible configured backend
  - error on ambiguity
- reserve a namespaced location for backend-specific settings without exposing concrete advanced backend options yet
- update diagnostics and documentation to use `backend` as the umbrella term, while reserving `provider` for more specific cases

## Rationale

This approach keeps the current user experience intact while removing the transport/model conflation that blocks future backend work. It also makes the resolution rules explicit, testable, and visible in diagnostics before any request is sent.

## Alternatives Considered

1. **Keep provider detection as the primary abstraction**

   Rejected because it preserves the existing coupling between transport choice and model selection.

2. **Require explicit backend selection everywhere**

   Rejected because it would unnecessarily break the current single-backend direct workflow.

3. **Add backend-specific controls immediately**

   Rejected because no in-scope backend needs them yet and the spec explicitly avoids surfacing unused complexity.

4. **Defer the abstraction until the first intermediary backend lands**

   Rejected because the current direct-backend flow already needs a cleaner internal model and deterministic validation.

## Consequences

### Positive

- Backend and model resolution can evolve independently.
- Ambiguity and incompatibility are validated before request submission.
- Future intermediary or routed backends can plug into the reserved backend abstraction.
- Diagnostics can explain what gmuse resolved and why.

### Negative

- Core resolution logic becomes more explicit and slightly more complex.
- Existing provider-oriented wording in docs, tests, and diagnostics will need to be updated.
- Some internal APIs will need to distinguish backend from model even when the current direct-backend path does not.

## Follow-up Work

- Define the concrete backend resolution helpers in the LLM/config path.
- Update diagnostics to surface resolved backend, resolved model, and resolution source.
- Add tests for ambiguity, explicit backend selection, and backend/model mismatch.
- Revisit the reserved backend-specific settings namespace when a later backend feature needs it.
