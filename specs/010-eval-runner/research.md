# Phase 0 Research: production-path eval runner

## Current planning baseline

- The eval program is split across multiple Speckit specs in `docs/planning/evals/implementation-plan.md`.
- Spec 009 is the fixture and suite foundation. It owns fixture schema, suite schema, stable case IDs, suite membership, temporary repository reconstruction, staged diff digest verification, and offline suite validation.
- This spec is the production-path runner slice. It starts only after fixtures and suites are validated by spec 009.
- Framework alignment update: use Inspect AI as the local eval framework
  candidate for task execution, sample logging, limits, and native analysis.
  gmuse owns the Git-backed fixture foundation and production-path solver.
- The runner must use real gmuse generation behavior rather than a parallel benchmark-only pipeline.
- Judge scoring, live-run budgeting/resume, baselines, fixture importing, and public recommendations are later specs.

## Research decisions

### 1. Boundary with fixture and suite foundation

**Decision**: Treat spec 009 fixture/suite validation as a required precondition
and consume its validated case objects, reconstructed staged repositories,
stable case IDs, and fixture revisions or digests as Inspect dataset/sample
metadata.

**Rationale**: The runner should not duplicate fixture ingestion, provenance validation, suite membership rules, or staged diff digest checks. Keeping that logic in spec 009 makes this slice smaller and prevents two sources of truth for fixtures.

**Alternatives considered**:

- Redefine a minimal fixture schema inside the runner. Rejected because it would drift from the foundation spec and make later importer/baseline work harder.
- Accept arbitrary paths to git repositories as runner input. Rejected for this slice because the acceptance focus is repeatable curated fixtures, not ad hoc local benchmarking.

### 1a. Local eval framework adoption

**Decision**: Adopt Inspect AI as the primary local eval framework candidate for
runner execution and logging. Represent each gmuse eval case as an Inspect
sample, run gmuse production generation through an Inspect solver, and record
generated messages, validation outcomes, prompt/context metadata, and
operational errors in Inspect logs.

**Rationale**: The high-level objective is not to build a general eval platform;
it is to evaluate gmuse's real commit-message behavior on controlled Git
fixtures. Inspect provides local task execution, scoring hooks, logs, limits,
and analysis patterns. Using those patterns avoids maintaining a parallel custom
artifact/logging system while preserving gmuse-specific fixture reconstruction
and production-path behavior.

**Alternatives considered**:

- Keep bespoke `run-plan.json`, `outputs.jsonl`, and `summary.json` as the
  canonical runner artifacts. Rejected because it duplicates framework
  responsibilities and makes later scoring/comparison fight Inspect rather than
  use it.
- Use a hosted/account-backed eval platform. Rejected because maintainer evals
  should remain local and not require a hosted service account.
- Use a prompt-matrix framework as the primary runner. Rejected for this slice
  because gmuse needs Python-level temporary repository reconstruction and
  production-path solver behavior.

### 2. Check/live CLI semantics

**Decision**: Use one maintainer command, `run --mode check|live`, under the
module entrypoint from spec 009. Check mode validates the selected suite, prints
the run plan, executes the Inspect-backed production-path runner pipeline with
deterministic local output, writes Inspect logs, and makes zero provider calls.
Live mode uses real candidate models and requires `--model`, plan display,
confirmation, and configured guardrails.

**Rationale**: A standalone preview mode is easy to confuse with implementation
planning and overlaps with check mode. Check mode gives maintainers a useful
preflight that proves fixture reconstruction, prompt/context creation,
validation, and Inspect logging without credentials or provider cost. Live mode
remains explicit and bounded.

**Alternatives considered**:

- Keep separate `plan` and `run` commands. Rejected because users must then
  understand a subtle distinction between previewing and offline execution.
- Use `--allow-live` in addition to a mode. Rejected because `--mode live` is
  already explicit and spec 011 will add richer confirmation behavior later.
- Use `offline` or `stub` mode names. Rejected because they imply provider
  simulation or model quality evaluation. `check` better communicates local
  pipeline verification.

### 3. Maintainer-only structure

**Decision**: Keep runner implementation in `tools/evals/gmuse_evals` with the
spec 009 validator and loader. Do not expose a public `gmuse eval` command.
Generated artifacts default under ignored `.gmuse-evals/runs/`.

**Rationale**: Evals are maintainer tooling, not ordinary product
functionality. Keeping orchestration outside `src/gmuse` avoids expanding the
installable package with draft eval behavior while still allowing the tool to
import production internals for fidelity.

**Alternatives considered**:

- Put runner modules under `src/gmuse/evals`: rejected for the same reason as
  spec 009; it makes maintainer tooling look like packaged product behavior.
- Add public `gmuse eval run`: rejected because the feature is not part of the
  normal user workflow.

### 4. Production generation invocation

**Decision**: The runner should call the same internal generation services used
by normal gmuse message generation through a lower-level
`generate_message_attempt()` path. Existing `generate_message()` keeps its
raising behavior. The internal attempt path preserves raw generated messages,
validation outcomes, prompt metadata, and operational errors.

**Rationale**: Calling internal services avoids CLI parsing noise while still
exercising the real git/context/prompt/provider/validation path. A lower-level
attempt result is needed because evals must preserve invalid raw outputs that
normal generation currently raises away. Instrumentation is acceptable only when
it observes behavior and does not alter prompt construction or validation rules.

**Alternatives considered**:

- Shell out to `gmuse msg` or another public command for every entry. Rejected because CLI stdout/stderr contracts make structured metadata capture fragile and slow.
- Build a separate eval prompt renderer. Rejected because it would evaluate different behavior from production.
- Catch `InvalidMessageError` from `generate_message()` only. Rejected because
  the raw generated message is no longer available at the right abstraction
  boundary.

### 5. Deterministic check output

**Decision**: Check mode uses one built-in deterministic local output policy
that returns a structurally valid message for the effective case format where
possible. Tests may inject invalid local output directly, but the CLI should not
expose a fake-model matrix.

**Rationale**: Check mode exists to test runner mechanics, not candidate model
quality. A single deterministic policy keeps the maintainer interface small
while still exercising production prompt construction, generation boundary,
validation, and artifact writing.

**Alternatives considered**:

- Expose `--offline-output valid|invalid`: rejected because it turns check mode
  into a fake provider framework.
- Require `--model` in check mode with model names such as `offline-static`:
  rejected because artifacts could be misread as model evidence.

### 6. Result artifact shape

**Decision**: Use Inspect logs as the canonical result artifact. Check and live
runs must attach explicit execution mode, candidate kind, suite/case/fixture
identity, production validation outcome, prompt/context metadata, and
operational error metadata to each Inspect sample result.

**Rationale**: Inspect already supplies local logs, analysis tools, and a data
model for eval runs. Storing gmuse metadata in Inspect logs makes later scoring
and strict safety comparison use the same source of truth that execution uses.
`candidate_kind` still lets later scoring skip deterministic check outputs.

**Alternatives considered**:

- Write custom JSONL files beside Inspect logs. Rejected as unnecessary unless
  the Inspect spike shows missing metadata or analysis gaps that cannot be
  solved through Inspect's log APIs.
- Store results in a database. Rejected because the initial maintainer workflow
  benefits from local files and no hosted/account-backed dependency.
- Use separate schemas for check and live artifacts. Rejected because check mode
  is meant to exercise the same Inspect task/log path as live mode.

### 7. Live call guard

**Decision**: Live mode requires preflight display, explicit maintainer
confirmation, and configured spend guardrails before provider calls. Prefer
Inspect-native limits such as sample, token, cost, time, or concurrency limits
where practical. A simple gmuse call/sample cap may be added only if Inspect
does not provide an adequate local guardrail for the selected provider path.

**Rationale**: The objective is to prevent runaway spend, not to maintain a
custom provider-call ledger. Aligning with Inspect limits keeps the design
simple while preserving explicit maintainer control before live calls.

**Alternatives considered**:

- Require exact custom `--max-calls` accounting. Rejected because it adds custom
  machinery before there is evidence that Inspect limits are insufficient.
- Add separate candidate and judge budgets: rejected because this command only
  makes candidate calls, and judge scoring is a later Inspect scorer concern.

### 8. Error classification boundary

**Decision**: Separate operational errors from deterministic production
validation outcomes. Initial operational categories are `auth_error`,
`rate_limit`, `timeout`, `network_error`, `context_length`, `empty_response`,
`fixture_setup_error`, and `unknown_error`. Continue after per-entry provider
errors, but fail before provider calls when suite or fixture validation fails.

**Rationale**: Provider/setup failures describe whether an entry ran successfully, not whether the generated commit message was good. Later scoring needs this distinction to avoid treating unavailable providers as low-quality messages.

**Alternatives considered**:

- Reuse the full scoring error taxonomy from eval requirements. Rejected because quality categories such as `hallucination` and `vague` belong to the judge/scoring phase, not this runner slice.
- Store only raw exception text. Rejected because summaries and future comparisons need stable categories.

### 9. Prompt and temporary repository privacy defaults

**Decision**: Record prompt hashes, prompt size, estimated tokens, and context
metadata by default; do not write raw prompt text into main result artifacts.
When `--preserve-debug` is selected, write raw prompts and preserved temporary
repositories under separate `debug/` paths.

**Rationale**: Eval fixtures may contain sensitive or adversarial text. Hashes and sizes support regression analysis without making prompt artifacts the default output. Debug preservation remains available for maintainers investigating failures.

**Alternatives considered**:

- Always write rendered prompts for reproducibility. Rejected because it increases privacy risk and artifact noise.
- Never allow prompt or repository preservation. Rejected because maintainers need an escape hatch for diagnosing failed fixture reconstruction or prompt construction.

### 10. Output directory and local automation behavior

**Decision**: Each invocation creates an independent output directory by
default using `.gmuse-evals/runs/<timestamp>-<suite>-<mode>/`. Explicit
`--output-dir` is allowed but must not contain existing runner artifacts. Do not
create `latest` symlinks or infer relationships between check and live runs.
Add a local-only `nox -s evals-check` convenience session that writes artifacts
to a temporary directory; do not add a live or check GitHub Actions workflow in
this slice.

**Rationale**: Independent directories avoid hidden state. Failing on existing
runner artifacts avoids accidental overwrite or append before spec 011 defines
resume behavior. A nox shortcut helps maintainers without exposing a live-call
CI path.

**Alternatives considered**:

- Infer live output directories from prior check runs: rejected because it
  creates hidden state.
- Add a `latest` symlink or pointer file: rejected because it is mutable state
  and has platform differences.
- Add check mode to default GitHub Actions immediately: rejected because pytest
  coverage can prove integration mechanics first, and repository automation
  should not expand around eval live-call tooling prematurely.

## Phase 1 implications

The design artifacts should encode:

- Inspect task/sample mapping from spec 009 validated fixtures;
- a case execution model that runs gmuse production generation from an Inspect
  solver;
- log metadata requirements instead of bespoke artifact contracts;
- operational error categories that stop short of judge/quality scoring;
- privacy defaults that store hashes and metadata rather than raw prompts;
- a single check/live CLI surface with live preflight, confirmation, configured
  limits, and no public `gmuse eval` command.
