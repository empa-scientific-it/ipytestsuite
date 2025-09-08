"""IPyTestSuite: Interactive testing suite for Jupyter notebooks with AI-powered explanations.

This package provides the %%ipytest cell magic for running pytest tests interactively
in Jupyter notebooks, with rich HTML output and optional AI-powered error explanations.

Usage:
    %load_ext ipytestsuite
    
    %%ipytest
    def solution_my_function(x):
        return x + 1
"""

from .magic import load_ipython_extension

__version__ = "0.1.0"
__author__ = "Edoardo Baldi"
__email__ = "edoardob90@gmail.com"

# Export the main entry point
__all__ = ["load_ipython_extension"]
