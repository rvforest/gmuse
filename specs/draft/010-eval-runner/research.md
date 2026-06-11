# Phase 0 Research: production-path eval runner

## Current planning baseline

- The eval program is split across multiple Speckit specs in `docs/planning/evals/implementation-plan.md`.
- Spec 009 is the fixture and suite foundation. It owns fixture schema, suite schema, stable case IDs, suite membership, temporary repository reconstruction, staged diff digest verification, and offline suite validation.
- This spec is the production-path runner slice. It starts only after fixtures and suites are validated by spec 009.
- The runner must use real gmuse generation behavior rather than a parallel benchmark-only pipeline.
- Judge scoring, live-run budgeting/resume, baselines, fixture importing, and public recommendations are later specs.

## Research decisions

### 1. Boundary with fixture and suite foundation

**Decision**: Treat spec 009 fixture/suite validation as a required precondition and consume its validated case objects, reconstructed staged repositories, stable case IDs, and fixture revisions or digests.

**Rationale**: The runner should not duplicate fixture ingestion, provenance validation, suite membership rules, or staged diff digest checks. Keeping that logic in spec 009 makes this slice smaller and prevents two sources of truth for fixtures.

**Alternatives considered**:

- Redefine a minimal fixture schema inside the runner. Rejected because it would drift from the foundation spec and make later importer/baseline work harder.
- Accept arbitrary paths to git repositories as runner input. Rejected for this slice because the acceptance focus is repeatable curated fixtures, not ad hoc local benchmarking.

### 2. Planning mode semantics

**Decision**: Planning mode resolves suites, cases, models, and config overrides into a run plan, validates fixture readiness, estimates prompt/context metadata where available, and writes no output records that look like completed generation attempts.

**Rationale**: Maintainers need a no-call preview before live execution. The plan should be concrete enough to review planned attempts and output paths but must be clearly distinct from real results.

**Alternatives considered**:

- Make planning mode emit placeholder JSONL output records. Rejected because future scoring/baseline tools could mistake placeholders for attempted case results.
- Skip fixture validation in planning mode. Rejected because a no-call plan should still catch fixture and suite problems before live runs.

### 3. Production generation invocation

**Decision**: The runner should call the same internal generation services used by normal gmuse message generation, with a narrow instrumentation seam for prompt hash, prompt size, estimated token count, context metadata, validation outcome, and timing.

**Rationale**: Calling internal services avoids CLI parsing noise while still exercising the real git/context/prompt/provider/validation path. Instrumentation is acceptable only when it observes behavior and does not alter prompt construction or validation rules.

**Alternatives considered**:

- Shell out to `gmuse msg` or another public command for every attempt. Rejected because CLI stdout/stderr contracts make structured metadata capture fragile and slow.
- Build a separate eval prompt renderer. Rejected because it would evaluate different behavior from production.

### 4. Result artifact shape

**Decision**: Write one JSONL output record per attempted case/model/config combination and one JSON summary per run. Both artifact types carry explicit schema versions.

**Rationale**: JSONL supports incremental writes and partial inspection, while a summary gives quick run-level counts and metadata. Schema versions allow later judge, resume, and baseline specs to validate compatibility.

**Alternatives considered**:

- Write one large JSON file with all records. Rejected because it is less robust for interrupted or large runs and encourages holding records in memory.
- Store results in a database. Rejected because the initial maintainer workflow benefits from simple inspectable files and no additional storage dependency.

### 5. Error classification boundary

**Decision**: Separate operational errors from deterministic production validation outcomes. Initial operational categories are `auth_error`, `rate_limit`, `timeout`, `network_error`, `context_length`, `empty_response`, `fixture_setup_error`, and `unknown_error`.

**Rationale**: Provider/setup failures describe whether an attempt ran successfully, not whether the generated commit message was good. Later scoring needs this distinction to avoid treating unavailable providers as low-quality messages.

**Alternatives considered**:

- Reuse the full scoring error taxonomy from eval requirements. Rejected because quality categories such as `hallucination` and `vague` belong to the judge/scoring phase, not this runner slice.
- Store only raw exception text. Rejected because summaries and future comparisons need stable categories.

### 6. Prompt and temporary repository privacy defaults

**Decision**: Record prompt hashes, prompt size, estimated tokens, and context metadata by default; do not write raw prompt text or preserve temporary repositories unless an explicit debug/preserve option is selected.

**Rationale**: Eval fixtures may contain sensitive or adversarial text. Hashes and sizes support regression analysis without making prompt artifacts the default output. Debug preservation remains available for maintainers investigating failures.

**Alternatives considered**:

- Always write rendered prompts for reproducibility. Rejected because it increases privacy risk and artifact noise.
- Never allow prompt or repository preservation. Rejected because maintainers need an escape hatch for diagnosing failed fixture reconstruction or prompt construction.

## Phase 1 implications

The design artifacts should encode:

- a run plan that is separate from result records;
- a case execution model that starts from spec 009 validated fixtures;
- artifact contracts with explicit schema versions;
- operational error categories that stop short of judge/quality scoring;
- privacy defaults that store hashes and metadata rather than raw prompts.
