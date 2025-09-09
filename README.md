# IPyTestSuite

Interactive testing suite for Jupyter notebooks with AI-powered explanations.

## Features

- **`%%ipytest` Cell Magic**: Run pytest tests directly in Jupyter notebook cells
- **Rich HTML Output**: Beautiful, interactive test results with collapsible sections
- **AI-Powered Explanations**: Get intelligent error explanations using OpenAI
- **Solution Tracking**: Automatically track test attempts and reveal solutions
- **AST-based Solution Extraction**: Parse and display reference solutions from test files
- **Pyodide Compatible**: Works in JupyterLite and browser-based environments

## Installation

```bash
# Using UV (recommended)
uv add ipytestsuite

# Using pip
pip install ipytestsuite
```

## Quick Start

1. Load the extension in your Jupyter notebook:

```python
%load_ext ipytestsuite
```

2. Use the `%%ipytest` magic to test your functions:

```python
%%ipytest
def solution_add_numbers(a, b):
    """Add two numbers together."""
    return a + b
```

The magic will automatically:
- Look for functions starting with `solution_`
- Find corresponding test files (`test_*.py`)
- Run pytest with the appropriate tests
- Display rich HTML results
- Offer AI explanations for failures (if configured)

## Configuration

### OpenAI Integration (Optional)

To enable AI-powered error explanations, create an `openai.env` file:

```bash
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL=gpt-4o-mini
OPENAI_LANGUAGE=English
```

### Test File Structure

The package expects test files following the pattern `test_<module_name>.py`. The test directory location can be configured using multiple methods:

```
your_project/
    notebook.ipynb
    tests/                    # Default location (or custom path)
       test_your_module.py    # Contains your tests
```

**Test Directory Configuration (in priority order):**
1. **Command-line argument**: `%%ipytest --path custom/tests`
2. **Environment variable**: `IPYTEST_PATH=path/to/tests`  
3. **Default**: `tests/` directory relative to current working directory

Test functions should be named `test_function_name` and reference functions should be named `reference_function_name`.

## Usage Examples

### Basic Testing

```python
%%ipytest
def solution_factorial(n):
    """Calculate factorial of n."""
    if n <= 1:
        return 1
    return n * solution_factorial(n - 1)
```

### Debug Mode

```python
%%ipytest --debug
def solution_buggy_function(x):
    return x / 0  # This will show debug info
```

### Async Testing

```python
%%ipytest --async
def solution_slow_function():
    import time
    time.sleep(1)
    return "done"
```

### Custom Test Module

```python
%%ipytest custom_module
def solution_my_function():
    return 42
```

### Custom Test Directory

```python
%%ipytest --path tutorial/tests
def solution_custom_path():
    return "tests from custom directory"
```

### Combined Options

```python
%%ipytest my_module --path custom/tests --debug --async
def solution_complex():
    return "all options combined"
```

## API Reference

### Magic Commands

The `%%ipytest` cell magic supports flexible argument parsing using CLI-style options:

**Basic Usage:**
- `%%ipytest`: Run tests with auto-detection (uses `__NOTEBOOK_FILE__` or requires explicit module name)

**Arguments:**
- `%%ipytest [module_name]`: Optional positional argument specifying the test module name

**Options:**
- `-p, --path PATH`: Specify custom test directory path
- `-d, --debug`: Enable debug mode with detailed test information  
- `--async`: Run tests asynchronously in background thread

**Examples:**
```python
%%ipytest                           # Auto-detect module, default settings
%%ipytest my_module                 # Specific module, default settings
%%ipytest --debug                   # Auto-detect module, debug enabled
%%ipytest --path custom/tests       # Auto-detect module, custom path
%%ipytest my_module --debug --async # All options combined
```

**Path Resolution Priority:**
1. `--path` command-line argument
2. `IPYTEST_PATH` environment variable
3. Default: `tests/` relative to current working directory

### Functions

- `load_ipython_extension(ipython)`: Main entry point for IPython extension

## Development

```bash
# Clone the repository
git clone https://github.com/yourusername/ipytestsuite.git
cd ipytestsuite

# Install in development mode
uv sync --dev

# Run tests
pytest
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
