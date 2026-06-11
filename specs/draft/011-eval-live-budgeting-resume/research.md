# Research: Eval Live Run Budgeting And Resume

## Decision: Require separate candidate and judge call budgets

**Rationale**: Candidate generation and judge scoring are different cost centers
with different provider credentials, models, and operational failure modes.
Separate budgets make it obvious which category is allowed to spend calls and
prevent judge work from consuming generation budget or vice versa.

**Alternatives considered**:

- Single total-call budget: rejected because it hides whether expensive judge
  work or candidate generation is responsible for planned calls.
- Optional budgets with defaults: rejected because live eval calls must be
  manual, explicit, and cost-controlled.
- Currency-based budget: deferred because provider prices change and this
  feature can provide a stable safety control with call counts.

## Decision: Count provider attempts against budgets

**Rationale**: A provider attempt can consume rate-limit capacity, quota, or
billable work even when the result is an operational error. Counting attempts is
the conservative behavior and keeps retry behavior from becoming an implicit
budget bypass if retries are added later.

**Alternatives considered**:

- Count only successful outputs: rejected because failed attempts can still cost
  money and time.
- Count completed records only: rejected because operational errors must still be
  visible in accounting.

## Decision: Display the same run plan for interactive and `--yes` modes

**Rationale**: `--yes` should remove the prompt, not the maintainer's visibility
into run size. The plan is also useful in logs for non-interactive maintainer
automation.

**Alternatives considered**:

- Suppress plan output with `--yes`: rejected because it makes accidental large
  runs harder to audit.
- Require interactive confirmation for all live runs: rejected because
  maintainers may run explicit budgeted jobs from controlled automation.

## Decision: Dry-run planning makes no provider calls and writes no live records

**Rationale**: Dry-run is for inspecting planned work and budget requirements.
Writing live output records during planning mode would blur record semantics and could
confuse resume compatibility.

**Alternatives considered**:

- Write a planning metadata artifact: rejected for this slice to keep resume based
  only on actual live run artifacts.
- Allow planning mode to precompute prompts through live providers: rejected
  because planning mode must be zero-call.

## Decision: Store candidate and judge records incrementally as append-only JSONL

**Rationale**: JSONL is already a natural fit for per-output eval records from
the production-path runner. Appending one completed item at a time preserves
work across interruption and keeps partial artifacts inspectable.

**Alternatives considered**:

- Rewrite one large JSON document after each item: rejected because interruption
  during rewrite has a larger corruption surface.
- Keep all records in memory and write at the end: rejected because it loses work
  on interruption.
- Store records in a database: rejected as unnecessary for maintainer-only local
  runs and inconsistent with the no-extra-runtime-dependencies direction.

## Decision: Maintain a JSON run summary alongside append-only records

**Rationale**: JSONL records are durable and inspectable, but maintainers need a
quick way to see whether a run is planned, running, interrupted, failed, or
complete. A summary can be rewritten after each item because records remain the
source of truth for completed work.

**Alternatives considered**:

- Derive all status only from JSONL: rejected because every status check would
  require scanning records and interpreting partial failures.
- Put summary fields into every record: rejected because it duplicates mutable
  aggregate state across many lines.

## Decision: Resume compatibility uses an explicit run identity fingerprint

**Rationale**: Resume must reject runs that would mix incompatible results.
Fingerprinting suite identity, fixture revisions, case selection, candidate
models, generation config, prompt version, judge config, rubric version, and
schema versions gives a concise compatibility check while preserving individual
fields for explainable mismatch messages.

**Alternatives considered**:

- Compare only command-line strings: rejected because config files, environment
  values, defaults, and schema versions can affect behavior without appearing in
  the visible command.
- Compare only output directory: rejected because the directory alone says
  nothing about semantic compatibility.
- Allow partial compatibility with warnings: rejected for this slice because a
  strict resume rule is safer and simpler.

## Decision: Completed records are skipped and never overwritten on resume

**Rationale**: Resume exists to avoid paying for completed work again. Preserving
original records maintains auditability and avoids accidental mutation of prior
generated messages or judge outputs.

**Alternatives considered**:

- Re-run completed records by default: rejected because it wastes live calls and
  changes result reproducibility.
- Overwrite records when regenerated: rejected because regeneration belongs to a
  new run or future explicit repair workflow, not resume.

## Decision: Judge call budgeting is supported without defining judge rubrics

**Rationale**: The eval sequence includes a later judge and scoring slice. This
feature can budget, plan, persist, and resume judge calls as opaque work items
once judge configuration exists, while leaving rubric structure and scoring
semantics to the judge feature.

**Alternatives considered**:

- Exclude judge calls completely: rejected because the user explicitly requested
  candidate and judge budget controls.
- Define judge rubric fields here: rejected because rubric design is out of
  scope and belongs to the judge/scoring spec.
