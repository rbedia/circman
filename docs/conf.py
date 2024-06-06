"""Sphinx configuration."""

project = "CircuitPython Manager"
author = "Rafael Bedia"
copyright = "2023, Rafael Bedia"  # noqa: A001
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_click",
    "myst_parser",
]
autodoc_typehints = "description"
html_theme = "furo"
