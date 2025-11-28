# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
from textwrap import dedent
from pathlib import Path


project = "gmuse"
copyright = "2025, Robert Forest"
author = "Robert Forest"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "autodoc2",
    "myst_parser",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosummary",
    "sphinx.ext.doctest",
]
myst_enable_extensions = [
    "colon_fence",
]
autodoc2_packages = [
    "../../src/gmuse",
]

doctest_test_doctest_blocks = ""

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
html_theme = "furo"
html_static_path = ["_static"]
# html_theme_options = {
#     "light_logo": "logo/package-logo-light.png",
#     "dark_logo": "logo/package-logo-dark.png",
# }

# Favicon configuration
# html_favicon = "_static/logo/favicon.png"
