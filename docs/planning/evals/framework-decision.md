# Maintainer Evals Framework Decision

Status: accepted planning decision

Date: 2026-06-14

## Decision

Use Inspect AI as the primary local eval framework for gmuse maintainer evals
where it substantially simplifies execution, logging, scoring, limits, and
analysis.

Do not use hosted or account-backed eval platforms as part of the default
maintainer workflow.

## Why

gmuse evals need more than a generic prompt-to-score loop. The eval harness must
reconstruct temporary Git repositories, stage changes, verify staged diff
digests, call gmuse's production generation path, preserve invalid generated
messages, and compare hard safety failures across runs.

Those requirements are gmuse-specific, but task execution, local logs, scorer
plumbing, model-graded scoring, limits, and analysis are common eval-framework
concerns. Inspect is a good candidate for those common concerns without forcing
a hosted service.

## Ownership Boundary

gmuse owns:

- fixture, case, suite, rubric, and provenance definitions;
- temporary Git repository reconstruction;
- staged diff digest verification;
- production-path generation through a gmuse solver;
- deterministic hard gates for validation, privacy, injection, and `max_chars`;
- strict safety comparison between eval runs.

Inspect should own:

- task and sample execution;
- local eval logs as canonical execution evidence;
- scorer orchestration;
- model-graded judge execution;
- native limits and analysis tools.

## Spike Outcome

The local Inspect spike confirmed that gmuse-shaped cases can be represented as
Inspect samples, a gmuse-owned generation wrapper can be represented as an
Inspect solver, deterministic hard gates can be represented as Inspect scorers,
and Inspect logs can preserve the metadata required for strict safety
comparison.

See `inspect-spike.md` for the prototype, results, and task-planning
implications.

## Consequences

- Inspect logs become the preferred source of truth for runner and scoring
  evidence.
- Custom `outputs.jsonl`, `scored-records.jsonl`, `judge-records.jsonl`, and
  custom resume ledgers are deferred unless an Inspect spike exposes a real
  metadata gap.
- Live run safety is framed as guardrails against runaway spend, not exact
  provider-call accounting.
- Resume is a convenience that should use framework support when practical, not
  a v1 custom subsystem.
- Named baseline promotion is deferred; v1 compares a reference Inspect log and
  a candidate Inspect log.
- The first automated gate is strict safety: fail on new hard failures and clear
  deterministic regressions, while reporting subjective judge score movement as
  evidence.

## Rejected Or Deferred Options

- **Custom eval platform**: rejected as the default path because it duplicates
  framework concerns and increases maintenance.
- **Hosted/account-backed platforms**: rejected for the default workflow because
  maintainer evals should remain local and account-free.
- **Prompt or red-team matrix tools as primary harness**: deferred unless a spike
  shows they preserve gmuse's Git-backed production-path boundary cleanly.
- **Exact `--max-calls` accounting**: deferred because the objective is runaway
  spend prevention, which can be satisfied by preflight display, confirmation,
  and configured limits.

## Spike Questions Resolved Before Task Planning

1. Validated spec 009 cases map cleanly to Inspect samples through a gmuse
   adapter.
2. gmuse production generation can be represented as an Inspect solver, with one
   implementation caveat: evals need a lower-level helper that preserves raw
   output before validation raises.
3. Deterministic hard gates and judge scoring fit Inspect scorers.
4. Inspect logs carry the metadata required for strict safety comparison.
5. Inspect limits are sufficient for live-run guardrails when gmuse requires at
   least one concrete bound before live calls.
