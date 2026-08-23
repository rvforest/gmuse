# Inspect AI Spike

Date: 2026-06-14

Status: completed

## Purpose

Verify whether Inspect AI can simplify the maintainer eval design without
forcing gmuse to give up the high-level objectives documented in specs 009-013.

The spike tested a local, no-provider-call path. Hosted/account-backed
frameworks remain out of scope.

## Package

Added `inspect-ai==0.3.239` through the `eval` dependency group:

```bash
uv add --group eval inspect-ai
```

This keeps Inspect out of gmuse runtime dependencies while making maintainer
eval tooling reproducible with:

```bash
uv run --group eval ...
```

## Prototype

Executable probe:

```text
docs/planning/evals/spikes/inspect_task_probe.py
```

Run command:

```bash
uv run --group eval python docs/planning/evals/spikes/inspect_task_probe.py
```

Observed output:

```text
status=success
synthetic-privacy-failure-001: value=I metadata={... 'privacy_leak': True ...}
synthetic-python-format-001: value=C metadata={... all hard gates false ...}
```

The generated Inspect log was then read back with `inspect_ai.log.read_eval_log`.
The log preserved:

- task-level gmuse metadata;
- sample IDs and sample metadata;
- raw generated message text in `sample.output.completion`;
- output metadata such as `gmuse_case_id`, staged diff digest, and prompt hash;
- score metadata containing deterministic hard-gate results.

## Findings

### 1. Spec 009 cases can map to Inspect samples

Inspect `Sample` supports `id`, `input`, `target`, `metadata`, files, setup, and
checkpoint configuration. That is enough for gmuse to keep its fixture and suite
schema while converting validated cases into Inspect samples at the runner
boundary.

gmuse should continue owning fixture validation and staged diff digest checks.
Inspect should receive only validated cases or fail samples explicitly when
preconditions do not hold.

### 2. gmuse generation fits as an Inspect solver

A custom solver can set `TaskState.output` to a `ModelOutput` carrying the
generated commit message and gmuse metadata. This is a good fit for the planned
production-path wrapper.

The main implementation detail is that current `generate_message()` validates
after the provider call and raises `InvalidMessageError` without returning the
raw invalid message. Since evals need to preserve invalid outputs, the runner
should use a small internal helper that separates:

- context gathering;
- prompt rendering;
- provider generation;
- raw output capture;
- production validation.

The user CLI can keep the current behavior. The eval solver just needs a lower
level call path that records the raw completion before validation is applied.

### 3. Hard gates and judge scoring fit as Inspect scorers

The prototype scorer emitted `Score(value=..., answer=..., explanation=...,
metadata=...)`. This is sufficient for deterministic gates such as:

- max chars exceeded;
- conventional format mismatch;
- privacy leak;
- severe instruction-injection obedience;
- production validation failure.

The same scorer mechanism should work for model-graded judge scoring. gmuse
still owns judge rubric semantics and hard-failure definitions.

### 4. Inspect logs can be canonical evidence

Inspect logs are suitable as the canonical runner/scoring artifact. The log API
round trip preserved the fields needed for strict safety comparison.

The comparison tool should use Inspect's Python log API rather than parsing log
JSON directly. That lets gmuse support both `.eval` and `.json` log formats.

### 5. Inspect limits are sufficient guardrails

Inspect exposes per-sample message, token, time, working-time, and cost limits,
plus eval-level sample limiting. This supports the guardrail objective: prevent
runaway spend with preflight, explicit confirmation, and configured bounds.

Cost limits depend on model cost data. For providers or local models without
reliable cost data, gmuse should require at least one non-cost bound such as
sample, token, time, or concurrency limits.

## Recommendation

Proceed with Inspect AI as the primary local eval framework for specs 010-013.

Keep these gmuse-owned pieces:

- fixture and suite schemas;
- fixture reconstruction and staged diff digest verification;
- production-path generation wrapper;
- deterministic hard gates;
- strict safety comparison.

Delegate these pieces to Inspect:

- task/sample execution;
- local logs;
- scorer orchestration;
- judge model calls;
- limit enforcement where Inspect has native support;
- log reading for comparison.

## Task Planning Implications

The first implementation slice should be:

1. Add fixture validation and a tiny smoke suite from spec 009.
2. Add an `inspect_adapter.py` that converts validated cases to `Sample`
   objects.
3. Add a gmuse eval generation helper that returns raw output plus validation
   status.
4. Add an Inspect task factory and solver that reconstructs each fixture,
   verifies the digest, calls the helper, and writes gmuse metadata into
   `ModelOutput`.
5. Add deterministic scorer(s) for hard gates.
6. Add a comparison command that reads two Inspect logs and fails on new hard
   failures.

Do not implement custom JSONL artifacts, custom resume ledgers, or named
baseline promotion in the first task plan unless Inspect exposes a concrete gap
during implementation.
