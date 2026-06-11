# Phase 0 Research: eval baselines and comparison

## Current planning baseline

- `docs/planning/evals/requirements.md` defines regression comparisons as
  pairwise candidate-versus-baseline evidence, including per-dimension deltas,
  per-case results, new hard failures, prompt size/token changes, first-shot
  success changes, and error category changes.
- `docs/planning/evals/implementation-plan.md` positions this feature as eval
  sequence item 5, after production-path result artifacts, live run budgeting,
  and judge/scoring.
- This feature depends on result artifacts from spec 010 and scored outputs from
  spec 012. It does not introduce fixture importing, live model calls, judge
  calls, retries, public recommendation pages, or hardcoded accept/reject gates.
- Evals remain maintainer-only. Normal package users should not pay dependency,
  credential, or runtime costs for baseline comparison tooling.

## Research decisions

### 1. Baseline promotion boundary

**Decision**: Promote baselines from completed, scored eval artifacts only.
Promotion creates a new versioned baseline artifact rather than renaming or
copying raw run output wholesale.

**Rationale**:

- Intentional promotion avoids accidental baselines from exploratory, failed, or
  partially resumed eval runs.
- A promoted artifact can preserve comparison-critical evidence while stripping
  debug-only and transient execution details by default.
- Requiring scored outputs from spec 012 ensures future comparisons can report
  score deltas, hard-failure flags, judge metadata, and manual override context.
- Requiring result metadata from spec 010 ensures generated messages, prompt
  hashes, validation outcomes, operational errors, model metadata, and config
  metadata remain tied to the production-path run.

**Alternatives considered**:

- Use raw result artifacts directly as baselines. Rejected because it makes
  accidental baseline creation too easy and would keep transient/debug fields as
  part of the comparison contract.
- Require a separate manual baseline file authored from scratch. Rejected because
  it would duplicate data already present in scored artifacts and increase drift.

### 2. Baseline artifact shape

**Decision**: Store a compact but complete baseline snapshot with:

- baseline schema version and creation metadata;
- source artifact references and source schema versions;
- suite ID/version, suite membership, case IDs, case revisions, and fixture
  revisions;
- model identity and resolved model metadata;
- generation config metadata;
- prompt version, prompt hash, prompt size, and estimated token metadata;
- generated messages and validation outcomes;
- deterministic check results, judge score metadata, judge prompt/model/rubric
  metadata, judge calibration metadata when available, manual
  annotation/override metadata, usability ratings, error categories,
  operational error categories, and hard-failure flags.

Debug-only fields are excluded by default and included only when the maintainer
explicitly opts into debug retention.

**Rationale**:

- Comparison must be reproducible offline from saved artifacts.
- Prompt hashes alone are not enough; prompt size and token estimates can reveal
  regressions even when score movement is small.
- Preserving judge and rubric metadata makes score deltas interpretable when
  scoring behavior changes.
- Preserving calibration metadata keeps judge setup quality visible when score
  deltas are reviewed later.
- Generated messages and concise rationales must remain inspectable so aggregate
  summaries do not hide per-case evidence.

**Alternatives considered**:

- Store only aggregate scores and summary counts. Rejected because it would not
  support pairwise regression review or hard-failure inspection.
- Store every field from raw runs. Rejected because debug/transient fields can
  include noisy, large, or private implementation details that are not needed for
  baseline comparison.

### 3. Judge calibration metadata

**Decision**: Preserve judge calibration metadata from scored artifacts when it
is available, and warn when baseline and candidate artifacts differ in
calibration report ID, expected label version, agreement values, parse failures,
or candidate-identity hiding.

**Rationale**:

- External LLM-as-judge research identifies position, verbosity, and
  self-preference risks in judge outputs.
- Spec 012 mitigates those risks with judge input controls and calibration
  reports.
- A score delta may reflect changed judge calibration rather than changed
  candidate behavior, so comparison must surface calibration differences.
- Calibration metadata is compact enough to preserve in baselines without
  retaining full debug prompts.

Sources: [MT-Bench/Chatbot Arena](https://arxiv.org/abs/2306.05685),
[G-Eval](https://arxiv.org/abs/2303.16634), and the
[position-bias study](https://arxiv.org/abs/2406.07791).

**Alternatives considered**:

- Ignore calibration metadata in baselines. Rejected because it hides judge setup
  quality from future comparisons.
- Require calibration for every promoted baseline in v1. Rejected because early
  maintainer baselines may be useful before the calibration set is mature.

### 4. Same-model regression compatibility

**Decision**: Same-model regression mode is the default comparison mode and
requires strict compatibility checks. Model identity and generation config
differences are high-severity incompatibilities. Other differences, such as
suite/case revisions, prompt version, judge version, rubric version, and schema
version, produce structured warnings that classify the report as clean,
degraded, benchmark, or invalid evidence.

**Rationale**:

- The main maintainer question is whether a code, prompt, validation, or context
  change improved or regressed behavior for the same model.
- Model/config changes can dominate output differences, so treating those as
  clean regression evidence would be misleading.
- Some mismatches are still useful for exploratory review, but the report must
  make the risk explicit.

**Alternatives considered**:

- Reject every mismatch. Rejected because exploratory comparisons and migration
  across schema versions can still produce useful evidence if clearly labeled.
- Warn only in prose. Rejected because tests and automation need structured
  warning categories and severity.

### 5. Different-model benchmark mode

**Decision**: Different-model comparison is supported only through an explicit
benchmark mode. In that mode, model differences are allowed and reported, but
suite, case, config, prompt, judge, scoring, and schema mismatches still produce
warnings. Reports remain private evidence and must not become public
recommendation pages.

**Rationale**:

- Maintainers need occasional model-to-model evidence for private decisions and
  future reference benchmarks.
- The same comparison engine can calculate pairwise deltas for different models,
  but the interpretation is different from a same-model regression.
- Explicit benchmark mode prevents accidental treatment of model swaps as
  generation-path regressions.

**Alternatives considered**:

- Disallow different-model comparison entirely. Rejected because it is useful for
  private benchmarking and is explicitly in scope.
- Allow different models in default comparison mode. Rejected because it weakens
  regression review semantics.

### 6. Pairwise delta reporting

**Decision**: Compare artifacts by stable case identity and report one pairwise
record per shared case, plus separate missing/extra case records. Each pairwise
record includes:

- baseline and candidate generated-message references;
- per-dimension score values and deltas;
- aggregate score delta when both artifacts provide compatible aggregate scores;
- hard-failure status changes;
- prompt hash and prompt size/token deltas;
- first-shot success delta;
- quality/compliance error category changes;
- operational error category changes;
- judge rationale and manual override references;
- compatibility warnings scoped to the case when applicable.

**Rationale**:

- Stable case matching keeps reports reviewable even when suite ordering changes.
- Missing and extra cases are important evidence, not silent omissions.
- Hard failures must be visible even when numeric scores improve.
- Operational failures should be separated from quality/compliance failures to
  avoid confusing provider reliability with message quality.

**Alternatives considered**:

- Compare only suite-level aggregate summaries. Rejected because it hides case
  regressions and hard failures.
- Require identical case sets. Rejected because partial exploratory comparisons
  can still be informative when missing/extra cases are clearly reported.

### 7. Report outputs and reproducibility

**Decision**: Generate a structured comparison report artifact that can be read
by humans and tests. The report should include summary sections, structured
warnings, pairwise records, missing/extra cases, source references, and schema
metadata. Report generation must never make live candidate or judge calls.

**Rationale**:

- Offline reproducibility keeps comparisons cheap, deterministic, and suitable
  for CI or local review without credentials.
- A structured report is easier to test and can support future rendered views
  without changing comparison semantics.
- Source references let maintainers trace a report back to the promoted baseline
  and candidate run.

**Alternatives considered**:

- Print comparison only to terminal. Rejected because maintainers need durable
  review artifacts and contract tests need stable output.
- Re-score during comparison. Rejected because comparison should reflect saved
  evidence, avoid live calls, and not mix scoring changes into comparison logic.
