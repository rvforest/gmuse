# Quickstart for eval judge scoring

## Prepare a candidate run

Install the development dependencies with `uv sync` and run the smoke suite.

```bash
uv run python -m tools.evals.gmuse_evals run --mode check --suite smoke
```

Set `candidate_log` to the Inspect log path printed by the runner. Check mode
uses synthetic outputs to exercise the scorer workflow. Use a completed live
candidate run when evaluating candidate model quality.

## Score deterministic gates

```bash
uv run python -m tools.evals.gmuse_evals score \
  --log "$candidate_log" --output .gmuse-evals/scored/smoke-offline.eval
```

Open each sample's `gmuse_deterministic` score metadata to see its checks,
hard gates, or unscored reason. Production validation, applicable character
limits, configured synthetic privacy and injection markers, and obvious extra
output can trigger a hard failure. Hard failures set usability to `unusable`.
Subjective ratings remain empty. This command makes zero provider calls.

## Plan and run live judge scoring

The example uses an OpenAI judge. Choose the provider and model you intend to
use and configure its gmuse credentials before executing the live command.

```bash
uv run python -m tools.evals.gmuse_evals score \
  --log "$candidate_log" --output .gmuse-evals/scored/smoke-judged.eval \
  --judge-model openai/gpt-4o-mini --limit-samples 5 --plan
```

Review the judge configuration, rubric revisions, call count, calibration
status, and destination. Remove `--plan` to run, then confirm interactively.
For non-interactive runs, pass `--yes` to confirm the displayed plan. The
positive sample cap must cover all planned new calls. Calls run serially with
a per-response `--max-tokens` and request `--timeout`. Run-wide token, cost,
and time limits are unavailable on the direct provider path.

In the scored log, inspect each sample's `gmuse_judge` score metadata for
named 1–4 ratings, rationales, usability, and hard gates. Judge provider and
parse failures have separate operational categories. Candidate failures with
no output and samples with missing or changed evidence have explicit unscored
reasons.

The judge ordinarily sees the candidate text without its provider or model.
The result flags self-judging independently. For diagnosis, `--judge-hard-failures`
includes hard-gated outputs and `--include-candidate-identity <reason>` includes
a recorded candidate identity. A hard gate continues to force unusable status
when a diagnostic call produces ratings.

### Keep the evidence with the candidate log

Keep the source candidate log and its adjacent `.gmuse-evidence/` and
`.gmuse-judge-responses/` directories together. The runner stores the exact
staged diff and context in the evidence directory. Scoring checks the stored
content digests and the rubric and profile identities before judging. The
response directory holds the original judge bodies, including malformed
responses. Both locator types resolve from the candidate log's directory,
even if the scored log is saved elsewhere. Treat these directories as private
working files.

Legacy candidate logs without evidence remain usable for deterministic
scoring. Rerun generation to capture evidence for live judging.

### Resume judging

If an interrupted or partially failed judging run wrote an Inspect log, use a
new output path and the same source log and judge settings.

```bash
uv run python -m tools.evals.gmuse_evals score \
  --log "$candidate_log" --output .gmuse-evals/scored/smoke-resumed.eval \
  --judge-model openai/gpt-4o-mini --resume .gmuse-evals/scored/smoke-judged.eval \
  --limit-samples 5 --plan
```

Compatible completed results are reused when their evidence and raw response
can be verified. Review the remaining calls, then remove `--plan` and confirm.
A new positive cap applies to the remaining attempts. If the interrupted
process produced no scored log, start a new bounded scoring run.

## Calibrate a judge

Build `CalibrationExample` records from manually labeled messages with an
exact, verified staged diff and the associated context. Use one rubric and
profile revision per report. Call `run_calibration` from
`tools.evals.gmuse_evals.calibration` with a fixed `JudgeConfiguration` and
`expected_label_version`. Supply a mock `provider_call` for offline testing.
To use the configured live judge, review the examples and pass
`confirmed=True` with a positive `limit_samples` covering all examples.

Write the returned report as JSON and pass it to scoring with
`--calibration-report path/to/report.json`. The report preserves expected and
observed labels, agreement by dimension, parse and operational failure counts,
and candidate identity controls. Scoring links the report when the judge,
rubric, profile, and candidate identity visibility match.

## Record manual review

Use `review_target` from `tools.evals.gmuse_evals.review_events` with the
sample's automated score metadata and the scored run ID
(`gmuse_scoring.scoring_run_id` in a judged log's metadata). For an offline
scored log, use its file SHA-256 as the stable run identifier.

Create a `ManualAnnotation` for a note or a `ManualOverride` with
`OverrideChanges` for an audited correction. Both take a target, reviewer,
and rationale and add a timestamp automatically. Use `append_review_event`
to save the event in a local review directory, then `load_review_events` and
`apply_review_events` to inspect the resulting effective scores. Inspect
continues to hold the original candidate and automated scoring evidence.
