import glob
import os
import shutil
from typing import Literal

import nox

# Define common tags for session organization
TEST_TAG = "test"
LINT_TAG = "lint"
FORMAT_TAG = "format"
DOCS_TAG = "docs"
CLEAN_TAG = "clean"

# Add a single source of truth for the Python testing matrix
TEST_PYTHON_VERSIONS: tuple[str, ...] = ("3.10", "3.11", "3.12", "3.13", "3.14")

nox.options.sessions = ["lint", "format", "types", "test"]

# ==================== CHECKS ====================


@nox.session(venv_backend="uv", tags=[LINT_TAG, FORMAT_TAG, TEST_TAG])
def check(session: nox.Session) -> None:
    """Run all checks (lint, formatting, type checking)."""
    session.run("uv", "run", "pre-commit", "run", "--all-files", *session.posargs)


@nox.session(venv_backend="uv", tags=[LINT_TAG])
def lint(session: nox.Session) -> None:
    """Check code with ruff linter."""
    session.notify("check", posargs=["lint"])


@nox.session(venv_backend="uv", tags=[FORMAT_TAG])
def format(session: nox.Session) -> None:
    """Format code with ruff."""
    session.notify("check", posargs=["format"])


@nox.session(venv_backend="uv", tags=[TEST_TAG])
def types(session: nox.Session) -> None:
    """Run static type checking."""
    session.notify("check", posargs=["types"])


@nox.session(venv_backend="uv")
def fix(session: nox.Session) -> None:
    """Fix formatting and linting"""
    _run_install(session, groups=["dev"])
    session.run("ruff", "check", "--fix")
    session.run("ruff", "format")


# ==================== TESTS ====================


@nox.session(venv_backend="uv", tags=[TEST_TAG], python=TEST_PYTHON_VERSIONS)
def test(session: nox.Session) -> None:
    """Run tests with pytest across multiple Python versions (3.10-3.13)."""
    _run_install(session)
    session.run("pytest", *session.posargs)


@nox.session(venv_backend="uv", tags=[TEST_TAG], python=TEST_PYTHON_VERSIONS)
def coverage(session: nox.Session) -> None:
    """Run tests with coverage reporting."""
    _run_install(session)
    session.run(
        "pytest",
        "--cov=src/gmuse",
        "--cov-branch",
        *session.posargs,
    )


# ==================== DOCUMENTATION ====================


@nox.session(venv_backend="uv", tags=[DOCS_TAG])
def docs(session: nox.Session) -> None:
    """Build the documentation."""
    _run_install(session, groups=["docs"])
    session.chdir("docs")
    session.run("sphinx-build", "-b", "html", "source", "build/html", *session.posargs)
    print("Documentation built.")


@nox.session(venv_backend="uv", tags=[DOCS_TAG])
def livedocs(session: nox.Session) -> None:
    """Sphinx autobuild"""
    _run_install(session, groups=["docs"])
    session.run(
        "sphinx-autobuild",
        "docs/source",
        "docs/build/html",
        *session.posargs,
    )


@nox.session(venv_backend="uv", tags=[DOCS_TAG])
def linkcheck(session: nox.Session) -> None:
    """Check documentation links."""
    _run_install(session, groups=["docs"])
    session.chdir("docs")
    session.run(
        "sphinx-build", "-b", "linkcheck", "source", "build/linkcheck", *session.posargs
    )


# ==================== CLEAN ====================


@nox.session(venv_backend="uv", python=False, tags=[CLEAN_TAG])
def clean(session: nox.Session) -> None:
    """Clean up build artifacts."""
    patterns = [
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "htmlcov",
        "*.egg-info",
        "dist",
        "build",
        ".coverage",
        "coverage.xml",
    ]

    for pattern in patterns:
        for path in (
            p
            for p in [*glob.glob(pattern), *glob.glob(f"**/{pattern}", recursive=True)]
            if os.path.exists(p)
        ):
            try:
                if os.path.isfile(path):
                    os.unlink(path)
                else:
                    shutil.rmtree(path)
                session.log(f"Removed: {path}")
            except Exception as e:
                session.error(f"Error removing {path}: {e}")

    # Clean docs build directory
    docs_build = os.path.join("docs", "build")
    if os.path.exists(docs_build):
        shutil.rmtree(docs_build)
        session.log(f"Removed: {docs_build}")


def _run_install(
    session: nox.Session, groups: list[Literal["main", "dev", "docs"]] = ["main", "dev"]
) -> None:
    cmd = ["uv", "sync"]
    group_arg = "--group" if "main" in groups else "--only-group"
    if "dev" in groups:
        cmd.append(f"{group_arg}=dev")
    if "docs" in groups:
        cmd.append(f"{group_arg}=docs")
    session.run_install(
        *cmd,
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
    )
