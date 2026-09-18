"""Sphinx configuration for the cerf documentation (https://immm-sfa.github.io/cerf).

Build locally with ``make html`` from the ``docs`` directory (requires ``pip install -e ".[docs]"``).

"""

import os
import sys
from importlib.metadata import PackageNotFoundError, version as _dist_version

sys.path.insert(0, os.path.abspath('../../'))

# -- Project information -----------------------------------------------------

project = 'cerf'
copyright = '2021-present, Battelle Memorial Institute'
author = 'Chris R. Vernon'

# single source of truth for the version is the installed distribution (pyproject.toml)
try:
    release = _dist_version("cerf")
except PackageNotFoundError:
    release = "0.0.0+unknown"

version = release

# -- General configuration ---------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.mathjax',
    'sphinx.ext.intersphinx',
    'sphinx.ext.githubpages',
    'sphinx.ext.autosectionlabel',
    'sphinx_design',
    'sphinx_copybutton',
]

templates_path = ['_templates']
exclude_patterns = ['**.ipynb_checkpoints', 'quickstarter.rst']
source_suffix = {'.rst': 'restructuredtext'}

# autodoc / napoleon
autodoc_member_order = 'bysource'
autodoc_typehints = 'description'
autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'show-inheritance': True,
}
napoleon_google_docstring = True
napoleon_numpy_docstring = True
autosummary_generate = False

# :ref:`Section title` links within and across pages; prefix with the document name to avoid clashes
autosectionlabel_prefix_document = False
autosectionlabel_maxdepth = 3

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'pandas': ('https://pandas.pydata.org/docs/', None),
    'geopandas': ('https://geopandas.org/en/stable/', None),
    'rasterio': ('https://rasterio.readthedocs.io/en/stable/', None),
    'joblib': ('https://joblib.readthedocs.io/en/stable/', None),
}

# copy button: strip prompts from copied code
copybutton_prompt_text = r">>> |\.\.\. |\$ |In \[\d*\]: | {2,5}\.\.\.: | {5,8}: "
copybutton_prompt_is_regexp = True

# -- Options for HTML output -------------------------------------------------

html_theme = 'furo'
html_title = f'cerf {release}'
html_short_title = 'cerf'
html_static_path = ['_static']
html_css_files = ['css/cerf.css']
html_favicon = '_static/cerf-mark.svg'
html_last_updated_fmt = '%Y-%m-%d'
html_show_sphinx = False
html_copy_source = False

html_theme_options = {
    'source_repository': 'https://github.com/IMMM-SFA/cerf/',
    'source_branch': 'main',
    'source_directory': 'docs/source/',
    'navigation_with_keys': True,
    'top_of_page_buttons': ['view', 'edit'],
    'light_css_variables': {
        'color-brand-primary': '#14665b',
        'color-brand-content': '#14665b',
        'color-brand-visited': '#14665b',
        'color-foreground-primary': '#203832',
        'color-foreground-secondary': '#4c625c',
        'color-foreground-muted': '#596c65',
        'color-background-primary': '#fcfcf9',
        'color-background-secondary': '#f0f3ec',
        'color-background-border': '#dbe3da',
        'color-sidebar-background': '#f3f5ef',
        'color-sidebar-link-text--top-level': '#203832',
        'color-sidebar-item-background--hover': '#e5ece2',
        'color-sidebar-item-expander-background--hover': '#dbe5d8',
        'color-highlight-on-target': '#edf2d6',
        'color-api-name': '#14665b',
        'color-api-pre-name': '#14665b',
        'color-api-background': '#edf2eb',
        'color-api-background-hover': '#e2ebdf',
        'font-stack': ('-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", '
                       'Arial, sans-serif'),
        'font-stack--monospace': ('ui-monospace, SFMono-Regular, Menlo, Consolas, '
                                  '"Liberation Mono", monospace'),
        'cerf-surface': '#ffffff',
        'cerf-tint': '#e9f0e3',
        'cerf-hero-background': '#edf3e7',
        'cerf-hero-text': '#173f35',
        'cerf-code-background': '#f1f4ee',
    },
    'dark_css_variables': {
        'color-brand-primary': '#9ad8bc',
        'color-brand-content': '#9ad8bc',
        'color-brand-visited': '#9ad8bc',
        'color-foreground-primary': '#e1eae3',
        'color-foreground-secondary': '#bccbc3',
        'color-foreground-muted': '#a6b8ad',
        'color-background-primary': '#14201d',
        'color-background-secondary': '#1d2d27',
        'color-background-border': '#34483d',
        'color-sidebar-background': '#182620',
        'color-sidebar-link-text--top-level': '#e1eae3',
        'color-sidebar-item-background--hover': '#2a3d32',
        'color-sidebar-item-expander-background--hover': '#34483d',
        'color-highlight-on-target': '#334b31',
        'color-api-name': '#9ad8bc',
        'color-api-pre-name': '#9ad8bc',
        'color-api-background': '#21332b',
        'color-api-background-hover': '#2a3d32',
        'cerf-surface': '#1b2b24',
        'cerf-tint': '#263c2f',
        'cerf-hero-background': '#233d30',
        'cerf-hero-text': '#e0efda',
        'cerf-code-background': '#1a2a23',
    },
    'footer_icons': [
        {
            'name': 'GitHub',
            'url': 'https://github.com/IMMM-SFA/cerf',
            'html': (
                '<svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 16 16">'
                '<path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 '
                '0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 '
                '1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15'
                '-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 '
                '2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 '
                '1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z"></path></svg>'
            ),
            'class': '',
        },
    ],
}

# -- Extension configuration -------------------------------------------------

mathjax3_config = {
    'tex': {'inlineMath': [['$', '$'], ['\\(', '\\)']]},
}
