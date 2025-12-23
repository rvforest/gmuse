# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import sys
from textwrap import dedent
from pathlib import Path


project = "gmuse"
html_title = "gmuse"
copyright = "2025, Robert Forest"
author = "Robert Forest"

# -- Path setup --------------------------------------------------------------
# Ensure gmuse (src/) and local Sphinx extensions (docs/_ext/) are importable.
REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = REPO_ROOT / "src"
EXT_DIR = REPO_ROOT / "docs" / "_ext"
sys.path.insert(0, str(SRC_DIR))
sys.path.insert(0, str(EXT_DIR))

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "autodoc2",
    "myst_parser",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosummary",
    "sphinx_copybutton",
    "sphinx_design",
    "sphinxcontrib.asciinema",
    "prompt_templates",
]
copybutton_prompt_text = "$ "
copybutton_only_copy_prompt_lines = True
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "fieldlist",
    "tasklist",
]
autodoc2_packages = [
    "../../src/gmuse",
]

templates_path = ["_templates"]
exclude_patterns = []  # type: ignore

autosummary_generate = True

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

myst_heading_anchors = 3

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# html_theme = 'sphinx_rtd_theme'
html_theme = "pydata_sphinx_theme"
html_static_path = ["_static"]
html_theme_options = {
    "logo": {
        "text": "gmuse",
        "image_light": "_static/logo/gmuse-logo-light.png",
        "image_dark": "_static/logo/gmuse-logo-dark.png",
    },
    "github_url": "https://github.com/rvforest/gmuse",
    "use_edit_page_button": True,
    "header_links_before_dropdown": 4,
}

html_context = {
    "github_user": "rvforest",
    "github_repo": "gmuse",
    "github_version": "main",
    "doc_path": "docs/source",
}

html_css_files = [
    "custom.css",
]

# Favicon configuration
html_favicon = "_static/gmuse-favicon.png"

# -- Options for linkcheck ---------------------------------------------------
# Handle permanent redirects
linkcheck_allowed_redirects = {
    r"https://github\.com/chrisjsewell/sphinx-autodoc2": r"https://github\.com/sphinx-extensions2/sphinx-autodoc2",
}

# Ignore specific links that are known to be valid but flagged by linkcheck.
# In this case `tutorials/quickstart.html` is reported as broken but works in the
# built docs; ignore only that exact path so other link issues still surface.
linkcheck_ignore = [
    r"tutorials/quickstart\.html$",
]
