# Spec 011 implementation handoff

The branch is based on `adcd95e` from `main`. Implementation and test drafts
are in place. Validation stopped after two machine crashes. See
[tasks.md](tasks.md) for the remaining checks.

## Changes in this branch

- Live `--plan` validates the same suite, matrix, limits, and log destination
  as execution. It shows each entry's effective settings and exits before
  confirmation, log directory creation, and Inspect execution.
- Live execution shows the plan before asking for confirmation. If stdin or
  stdout is redirected, the caller must pass `--yes`. The explicit positive
  sample cap still covers the entire matrix.
- Preview and execution share read-only destination checks. Only execution
  creates the Inspect log directory.
- The offline `evals-check` session uses LiteLLM's bundled price map. Inspect's
  dependency was otherwise attempting an import-time GitHub fetch.
- Added tests for zero-call preview, rejection and confirmation order, matrix
  counts, interrupted Inspect logs, and fresh reruns. All live tests use mocks.
  The reuse decision and maintainer workflows are documented.

## Verification state

- The 13 existing live, check, and automation tests passed before the changes.
  The sandbox needed writable `XDG_CACHE_HOME` and `XDG_DATA_HOME` paths for
  Inspect.
- An initial focused run collected the old cancellation test before its
  terminal mock was added. Both cancellation variants failed. The test now
  simulates an interactive terminal. A completed rerun was unavailable.
- Ruff lint and formatting passed for the implementation files. Final Nox
  test, documentation build, and coverage results are pending.
  The attempted offline Nox matrix lacked Python 3.11 and 3.12 and the cached
  Python 3.13 zstandard wheel.
- Inspect 0.3.290's retry and sample lookup were inspected in the installed
  source. Reuse is deferred because the current task cannot be reconstructed
  by native retry and Inspect does not verify per-entry staged diff and prompt
  hashes. T013 and T014 are conditional and do not apply.

## Resume on the next machine

1. Run `uv sync`, then the focused tests below. If the environment restricts
   writes to the home directory, give Inspect writable XDG cache and data
   directories. The LiteLLM switch keeps the price map local during tests.

   ```bash
   LITELLM_LOCAL_MODEL_COST_MAP=True uv run pytest \
     tests/unit/test_eval_runner_plan.py \
     tests/integration/test_eval_live_guardrails.py \
     tests/integration/test_eval_runner_live.py \
     tests/integration/test_eval_runner_logs.py \
     tests/integration/test_eval_runner_check.py \
     tests/contract/test_eval_runner_automation.py
   ```

2. Confirm the SIGINT test in `test_eval_runner_logs.py` opens a cancelled
   native log and recovers the first completed message. Adjust native logging
   only if that test exposes a gap.
3. Finish T009. The existing automation contract test checks only workflows
   using `.yml`, while the main CI workflow uses `.yaml`. Cover both and assert
   that the offline Nox session uses check mode, cleared credential variables,
   and the bundled price map.
4. Run the [quickstart](quickstart.md) preview, offline smoke, and mocked
   scenarios, then run the Nox lint, type, test, docs, and diff-coverage checks.
   Update the task checklist after validation.
