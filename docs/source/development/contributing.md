# Contributing

Thank you for your interest in contributing to gmuse! This guide outlines project-specific requirements and workflows.

## Setting Up Your Development Environment

### Prerequisites

- Python 3.11 or higher
- Git
- A GitHub account

We assume you are familiar with basic git workflows (forking, cloning, branching, committing, pushing, and pull requests). For a refresher, see [GitHub's documentation](https://docs.github.com/en/get-started/start-your-journey).

### Fork and Clone the Repository

- Fork the repository on GitHub.
- Clone your fork to your local machine.
- Add the original repository as an upstream remote.

### Create a Development Environment

1. Download and install uv. See the [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/) for instructions.
2. Create and activate a virtual environment and install project and dev dependencies:

   ```bash
   uv sync
   ```

   This sets up a virtual environment, installs the required dependencies, and configures nox for running tests and other tasks.

## Development Workflow

- Create a new branch for your feature or bugfix.
- Make your changes and add tests.
- Ensure all tests pass:

    ```bash
    uv run nox -s test
    ```

- Check code quality:

   ```bash
   uv run nox -s lint
   ```

- Commit and push your changes to your fork.
- Open a pull request on GitHub and fill out the pull request template.

## Coding Standards

### Code Style

We use [Ruff](https://docs.astral.sh/ruff/) for both code formatting (Black-compatible rules) and linting.
Format your code with:

```bash
uv run nox -s format
```

Check for linting issues with:

```bash
uv run nox -s lint
```

To check formatting without making changes:

```bash
uv run nox -s format -- --check
```

To run all linting and formatting checks:

```bash
uv run nox -s check
```

### Type Hints

Use type hints throughout the codebase. Example:

```python
def example_function(param1: str, param2: int) -> bool:
    """Example function with type hints."""
    return len(param1) > param2
```

### Documentation

All public functions, classes, and methods should have docstrings following the [Google style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings):

```python
def example_function(param1: str, param2: int) -> bool:
    """Example function with Google style docstring.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When param1 is empty
    """
    if not param1:
        raise ValueError("param1 cannot be empty")
    return len(param1) > param2
```

## Pre-commit Hooks

We optionally support [pre-commit](https://pre-commit.com/) hooks to help catch formatting and linting issues before you commit.
To enable pre-commit hooks locally, install pre-commit and run:

```bash
uv run pre-commit install
```

This installs both the `pre-commit` and `pre-push` hook types.
If you already have hooks installed from an older clone, add the pre-push hook with:

```bash
uv run pre-commit install --hook-type pre-push
```

The commit hooks run linting and formatting on staged files.
The pre-push hook runs `nox -s diff-coverage` so a push is blocked when changed lines are under the Codecov patch target (90%).
The hook is skipped in CI, where Codecov is the patch-coverage gate.
Use of pre-commit is optional; the GitHub Actions workflow is the final gatekeeper for code quality. All code must pass the checks enforced by CI before it is accepted, regardless of local pre-commit usage.

## Dependency Updates

`.github/dependabot.yml` only schedules monthly version updates, and for Python packages it only refreshes `uv.lock` within the ranges in `pyproject.toml`.
Security fixes come from a repository setting instead, so turn on **Dependabot alerts** and **Dependabot security updates** in the repository's Settings > Advanced Security.

## GitHub Actions

We use [GitHub Actions](https://docs.github.com/en/actions) for continuous integration (CI).
All pull requests and pushes trigger automated workflows that check code formatting, linting, and run the test suite.
Your code must pass all required checks before it can be merged.

The main checks include:

- Code formatting and linting (using Ruff and pre-commit)
- Running the test suite

You can view the status of these checks on your pull request page under the "Checks" tab.

## Testing

### Maintainer-only eval fixtures

The offline eval foundation lives under `tools/evals/` and `evals/`; it is not
part of the public `gmuse` CLI. After changing a fixture, scoring profile,
rubric, case, or suite, validate it without provider credentials:

```bash
uv run python -m tools.evals.gmuse_evals validate --suite smoke
```

Use `--suite core` for the curated superset and `--strict-composition` when
advisory composition-goal shortfalls should fail the command. The report keeps
validation status and errors separate from a counted `Suite composition` section
covering Changes, Output formats, Context variations, Safety scenarios, and
Fixture sources. A case can contribute to multiple entries, such as one entry
for each supported output format.

Validation reconstructs a temporary Git repository, applies and stages the
complete patch, and compares the exact staged-diff digest and changed paths. It
makes no model, judge, or network calls.

Real and adapted fixtures record source-license evidence separately from
maintainer redistribution review; this metadata check is not legal approval.
All asset documents use schema `1.0`; supported SPDX expressions, absolute
HTTP(S) source/commit URLs, and `LicenseRef-*` values are checked during
validation. License evidence paths must be safe and repository-relative. Safety
fixtures must identify both an injection pattern and a location, and mark any
secret-like test values fake or nonfunctional. Rubrics use the shared
`commit-message-v1` profile's named 1–4 anchors, categorical usability labels,
independently assessable criteria, and objective gates. Deterministic gates are
limited to production validation, applicable length, known fake-secret leakage,
and configured literal injection markers; semantic instruction obedience is
reserved for later judge scoring. Selected-graph errors are aggregated, and
temporary repositories discard inherited Git configuration and Git-specific
environment behavior. See `specs/009-eval-fixtures-and-suites/quickstart.md`
for provenance, rubric, digest-failure, and suite-scoped loading examples.

### Writing Tests

We use [pytest](https://docs.pytest.org/) for testing. Place your tests in the `tests/` directory, mirroring the structure of the `src/` directory.

### Running Tests

Run the test suite with:

```bash
uv run nox -s test
```

Or run specific tests with:

```bash
uv run pytest tests/test_some_module.py
```

### Test Coverage

Check coverage with:

```bash
uv run nox -s coverage
```

To check coverage of the current diff against `origin/main` (the same 90% patch target Codecov uses):

```bash
uv run nox -s diff-coverage
```

For a stacked PR, set `DIFF_COVER_COMPARE_BRANCH` (for example
`DIFF_COVER_COMPARE_BRANCH=origin/other-branch uv run nox -s diff-coverage`).
Arguments after `--` are forwarded to pytest.
The session is skipped when `CI` is set; Codecov is the patch-coverage gate in CI.

## Building and Previewing Documentation

### Building Documentation

Build the documentation locally with:

```bash
uv run nox -s docs
```

The built documentation will be in the `docs/build/html/` directory.

### Previewing Documentation

You can preview the documentation by opening `docs/build/html/index.html` in your browser or by running:

```bash
python -m http.server -d docs/build/html
```

Or preview live docs by running:

```bash
uv run nox -s livedocs
```

Then visit `http://localhost:8000` in your browser.

## Spell Checking Documentation

All Markdown documentation files (`.md`) in the `docs/` directory are automatically spell checked using [cspell](https://cspell.org/) as part of the pre-commit hooks and continuous integration process. This helps ensure that the documentation is clear and free of typographical errors.

**Note:** Only Markdown documentation files are spell checked. Source code files (e.g., `.py`) are not checked for spelling errors.

If you encounter a false positive (a word flagged as a typo that is actually correct, such as a technical term, acronym, or project-specific word), you can add it to the shared `cspell.json` configuration file in the project root. This file contains a list of allowed custom words for the project. To add a new word:

1. Open `cspell.json` in the project root.
2. Add your word to the `"words"` array, keeping the list in alphabetical order if possible.
3. Commit the change along with your documentation update.

Example:

```json
{
  "version": "0.2",
  "words": [
    "apidocs",
    "autodoc",
    "yournewword"  // Add your word here
  ]
}
```

This ensures that the word will not be flagged as a typo in future documentation builds or pre-commit checks.

**Tip for VS Code users:**

If you use the CSpell extension in VS Code, you can quickly add a flagged word to the project's `cspell.json` using the Quick Fix menu:

1. Hover over the underlined word flagged as a spelling error in your Markdown file.
2. Click the lightbulb icon, right-click and select "Quick Fix...", or press Ctrl+. (Windows/Linux) or Cmd+. (Mac) to open the Quick Fix menu.
3. Choose "Add to cspell.json" from the menu.
4. The word will be automatically added to the `words` array in `cspell.json` in your project root.

Do **not** choose "Add to workspace settings" or "Add to user settings" as this will not update the project's shared configuration file.

## Getting Help

If you need help with contributing to gmuse, you can:

- Open an issue on GitHub
- Reach out to the maintainers
- Join our community discussions

Thank you for contributing to gmuse!

# Maintainer eval runner

The production-path eval runner is maintainer-only tooling. Install the
development group with `uv sync`, then validate and run the offline smoke suite:

```bash
uv run python -m tools.evals.gmuse_evals validate --suite smoke
uv run python -m tools.evals.gmuse_evals run --mode check --suite smoke
```

Check mode uses deterministic local responses, exercises the real Git/context/
prompt/validation path, writes Inspect logs under `.gmuse-evals/inspect/`, and
makes zero provider calls. Generated logs and debug artifacts are ignored by
Git. Raw prompts are excluded from ordinary logs; use `--preserve-debug` only
when troubleshooting and treat the resulting `.gmuse-evals/debug/` files as
sensitive.

Apply deterministic scoring to a candidate log from the current runner with a
new output path. Rerun the eval if the log uses an older schema.

```bash
uv run python -m tools.evals.gmuse_evals score \
  --log ".gmuse-evals/inspect/<candidate-log>.eval" \
  --output .gmuse-evals/scored/smoke.eval
```

The command makes zero provider calls and writes a separate Inspect log.
Open the `gmuse_deterministic` score metadata for each sample to see its checks,
hard gates, or unscored reason. Hard failures set usability to `unusable`.
Subjective ratings require the judge scoring workflow.

Live runs require explicit model selection, a positive sample cap covering the
entire selected matrix. Preview the work before making provider calls with
`--plan`:

```bash
uv run python -m tools.evals.gmuse_evals run \
  --mode live --suite smoke --model gpt-4.1-mini \
  --limit-samples 5 --plan
```

The preflight displays the suite revision, selected cases and models, planned
entries, sample cap, privacy-safe effective settings for each entry, and log
destination. `--plan` makes no provider calls and creates no live logs or
results. For an actual run, omit `--plan`; the CLI displays the same plan before
asking for confirmation. Both stdin and stdout must be TTYs for the prompt, or
pass `--yes` for a non-interactive run.

Execution is serial. Token, cost, and wall-clock run limits are rejected because
Inspect cannot enforce them on gmuse's direct provider calls. Use
`--limit-samples` to bound attempts and `--max-tokens` to cap each response;
these do not promise a dollar budget. A sample cap smaller than the selected
matrix fails before provider calls. Inspect's native retry cannot reconstruct
gmuse's ephemeral task closure or verify staged-diff and rendered-prompt
hashes, so safe reuse is deferred; an interrupted bounded run may generate
completed entries again.

Live execution is not wired into the default GitHub workflows. The optional
local convenience command `uv run nox -s evals-check` runs only the offline
smoke check with a temporary Inspect log directory. The mocked live preflight
and confirmation scenarios can be run without credentials:

```bash
uv run pytest tests/integration/test_eval_live_guardrails.py tests/integration/test_eval_runner_live.py
```

## Judge and review saved evals

Use the scoring plan to see how many candidate messages would go to a live
judge. Set `candidate_log` to the path reported by the runner.

```bash
uv run python -m tools.evals.gmuse_evals score \
  --log "$candidate_log" --output .gmuse-evals/scored/smoke-judged.eval \
  --judge-model openai/gpt-4o-mini --limit-samples 5 --plan
```

Remove `--plan` and confirm when ready. Use `--yes` for non-interactive
execution. The scorer calls the judge serially for eligible samples with
verified evidence. It skips deterministic hard failures by default.
`--resume <previous-scored-log>` reuses compatible results and applies the
explicit call cap to the remaining attempts.

Keep the source candidate log and its adjacent `.gmuse-evidence/` and
`.gmuse-judge-responses/` directories together. These directories hold the
exact judge inputs and original judge response bodies. Regular Inspect score
metadata holds their content digests and locators, the named ratings,
rationales, hard gates, and operational status.
