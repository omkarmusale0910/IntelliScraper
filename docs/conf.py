# Configuration file for the Sphinx documentation builder.
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

# Add project root to path so autodoc can find the package.
sys.path.insert(0, os.path.abspath(".."))

# Project information 

project = "IntelliScraper"
copyright = "2025, Omkar Musale"
author = "Omkar Musale"
release = "0.2.0"

# General configuration 

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "myst_parser",
]

# Napoleon settings (Google-style docstrings)
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False

# Autodoc settings
autodoc_member_order = "bysource"
autodoc_typehints = "description"
autodoc_default_options = {
    "members": True,
    "show-inheritance": True,
    "undoc-members": False,
}

# Autosummary
autosummary_generate = False

# MyST parser for .md files
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

# Intersphinx mapping for cross-referencing
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# Options for HTML output 

html_theme = "furo"
html_title = "IntelliScraper"
html_static_path = ["_static"]

# Furo theme options
html_theme_options = {
    "source_repository": "https://github.com/omkarmusale0910/IntelliScraper",
    "source_branch": "main",
    "source_directory": "docs/",
}
