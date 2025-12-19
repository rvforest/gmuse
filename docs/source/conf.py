# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
from textwrap import dedent
from pathlib import Path


project = "gmuse"
html_title = "gmuse"
copyright = "2025, Robert Forest"
author = "Robert Forest"

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

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# html_theme = 'sphinx_rtd_theme'
html_theme = "sphinx_book_theme"
html_static_path = ["_static"]
html_theme_options = {
    "path_to_docs": "docs/source",
    "repository_url": "https://github.com/rvforest/gmuse",
    "repository_branch": "main",
    "use_repository_button": True,
    "use_edit_page_button": True,
    "use_issues_button": True,
    "home_page_in_toc": True,
    "logo": {
        "image_light": "_static/logo/gmuse-logo-light.png",
        "image_dark": "_static/logo/gmuse-logo-dark.png",
    },
}

html_css_files = [
    "custom.css",
]

# Favicon configuration
# html_favicon = "_static/logo/favicon.png"
