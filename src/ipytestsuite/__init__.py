"""
ipytestsuite - A Python package for running pytest in Jupyter notebooks.

This package provides a Jupyter cell magic %%ipytest for running pytest tests
directly in notebook cells, with AI-powered explanations for failed tests.

Usage:
    %reload_ext ipytestsuite

    %%ipytest
    def solution_my_function():
        return "Hello, World!"
"""

import importlib.metadata

from .testsuite import load_ipython_extension  # noqa

# Package metadata
__version__ = importlib.metadata.version("ipytestsuite")
__author__ = "Edoardo Baldi"
__email__ = "edoardob90@gmail.com"
__description__ = "A Python package for running pytest Jupyter notebooks, geared towards Python tutorials"

__all__ = [
    "load_ipython_extension",
    "__version__",
]
