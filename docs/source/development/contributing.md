# Contributing

Thank you for your interest in contributing to gmuse! This guide outlines project-specific requirements and workflows.

## Setting Up Your Development Environment

### Prerequisites

- Python 3.10 or higher
- Git
- A GitHub account

We assume you are familiar with basic git workflows (forking, cloning, branching, committing, pushing, and pull requests). For a refresher, see [GitHub's documentation](https://docs.github.com/en/get-started/quickstart).

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

We use [Ruff](https://github.com/charliermarsh/ruff) for both code formatting (Black-compatible rules) and linting.
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

This will automatically run code quality checks on staged files before each commit.
Use of pre-commit is optional; the GitHub Actions workflow is the final gatekeeper for code quality. All code must pass the checks enforced by CI before it is accepted, regardless of local pre-commit usage.

## GitHub Actions

We use [GitHub Actions](https://docs.github.com/en/actions) for continuous integration (CI).
All pull requests and pushes trigger automated workflows that check code formatting, linting, and run the test suite.
Your code must pass all required checks before it can be merged.

The main checks include:

- Code formatting and linting (using Ruff and pre-commit)
- Running the test suite

You can view the status of these checks on your pull request page under the "Checks" tab.

## Testing

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
