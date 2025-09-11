"""A module to define the `%%ipytest` cell magic"""

import argparse
import ast
import dataclasses
import inspect
import io
import os
import pathlib
from collections import defaultdict
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from queue import Queue
from threading import Thread
from typing import TYPE_CHECKING

import pytest
from IPython.core.interactiveshell import InteractiveShell
from IPython.core.magic import Magics, cell_magic, magics_class
from IPython.display import HTML, display

from .ast_parser import AstParser
from .exceptions import (
    FunctionNotFoundError,
    InstanceNotFoundError,
    NotebookContextMissingError,
    PytestInternalError,
)

# Import AI dependencies for type checking
if TYPE_CHECKING:
    from .ai_helpers import OpenAIWrapper
    from .exceptions import OpenAIWrapperError

# Try to import AI-related dependencies at runtime
try:
    from dotenv import find_dotenv, load_dotenv

    from .ai_helpers import OpenAIWrapper
    from .exceptions import OpenAIWrapperError

    HAS_AI_SUPPORT = True
except ImportError:
    HAS_AI_SUPPORT = False

    # Dummy functions to prevent NameError
    def find_dotenv(*args, **kwargs): ...

    def load_dotenv(*args, **kwargs): ...

    OpenAIWrapper = None  # type: ignore
    OpenAIWrapperError = Exception  # type: ignore
from .helpers import (
    AFunction,
    DebugOutput,
    FunctionInjectionPlugin,
    IPytestOutcome,
    IPytestResult,
    ResultCollector,
    TestOutcome,
    TestResultOutput,
)


def run_pytest_for_function(
    module_file: pathlib.Path, function: AFunction
) -> IPytestResult:
    """
    Runs pytest for a single function and returns an `IPytestResult` object
    """
    with redirect_stdout(io.StringIO()) as _, redirect_stderr(io.StringIO()) as _:
        # Create the test collector
        result_collector = ResultCollector()

        # Run the tests
        result = pytest.main(
            ["-k", f"test_{function.name}", f"{module_file}"],
            plugins=[
                FunctionInjectionPlugin(function.implementation),
                result_collector,
            ],
        )

    match result:
        case pytest.ExitCode.OK:
            return IPytestResult(
                function=function,
                status=IPytestOutcome.FINISHED,
                test_results=list(result_collector.tests.values()),
            )
        case pytest.ExitCode.TESTS_FAILED:
            if any(
                test.outcome == TestOutcome.TEST_ERROR
                for test in result_collector.tests.values()
            ):
                return IPytestResult(
                    function=function,
                    status=IPytestOutcome.PYTEST_ERROR,
                    exceptions=[
                        test.exception
                        for test in result_collector.tests.values()
                        if test.exception
                    ],
                )

            return IPytestResult(
                function=function,
                status=IPytestOutcome.FINISHED,
                test_results=list(result_collector.tests.values()),
            )
        case pytest.ExitCode.INTERNAL_ERROR:
            return IPytestResult(
                function=function,
                status=IPytestOutcome.PYTEST_ERROR,
                exceptions=[PytestInternalError()],
            )
        case pytest.ExitCode.NO_TESTS_COLLECTED:
            return IPytestResult(
                function=function,
                status=IPytestOutcome.NO_TEST_FOUND,
                exceptions=[FunctionNotFoundError()],
            )

    return IPytestResult(
        status=IPytestOutcome.UNKNOWN_ERROR, exceptions=[Exception("Unknown error")]
    )


def run_pytest_in_background(
    module_file: pathlib.Path,
    function: AFunction,
    test_queue: Queue,
):
    """Runs pytest in a background thread and puts the result in the provided queue"""
    test_queue.put(run_pytest_for_function(module_file, function))


@magics_class
class TestMagic(Magics):
    """Class to add the test cell magic"""

    def __init__(self, shell):
        super().__init__(shell)
        self.shell: InteractiveShell = shell
        self.cell: str = ""
        self.module_file: pathlib.Path | None = None
        self.module_name: str | None = None
        self.threaded: bool | None = None
        self.test_queue: Queue[IPytestResult] | None = None
        self.cell_execution_count: dict[str, dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        self._orig_traceback = self.shell._showtraceback  # type: ignore
        # This is monkey-patching suppress printing any exception or traceback

    def parse_magic_args(self, line: str) -> tuple[str, pathlib.Path, bool, bool]:
        """Parse the magic arguments and return the module name and file path."""
        parser = argparse.ArgumentParser(prog="%%ipytest", add_help=False)
        parser.add_argument("module", nargs="?", default=None, help="Module name")
        parser.add_argument("-p", "--path", help="Path to test directory")
        parser.add_argument(
            "--async",
            action="store_true",
            dest="is_async",
            default=False,
            help="Run tests asynchronously",
        )
        parser.add_argument(
            "-d",
            "--debug",
            action="store_true",
            dest="is_debug",
            default=False,
            help="Enable debug mode",
        )

        try:
            args, _ = parser.parse_known_args(line.strip().split())
        except (SystemExit, argparse.ArgumentError):
            raise

        # Module name is either passed as argument (override) or inferred from __NOTEBOOK_FILE__
        if (module_name := args.module) is None:
            # Look for the variable __NOTEBOOK_FILE__ injected by JupyterLab extension
            notebook_file = self.shell.user_global_ns.get("__NOTEBOOK_FILE__")

            if notebook_file is None:
                raise NotebookContextMissingError

            module_name = str(notebook_file).removesuffix(".ipynb")

        # Test path resolution:
        # 1. Environment variable IPYTEST_PATH
        # 2. Magic line command-line argument "--path" or "-p"
        # 3. Default to Path.cwd() / "tests"
        if os.environ.get("IPYTEST_PATH"):
            test_path = pathlib.Path(os.environ["IPYTEST_PATH"])
        elif args.path:
            test_path = pathlib.Path(args.path)
        else:
            test_path = pathlib.Path.cwd() / "tests"

        return module_name, test_path, args.is_debug, args.is_async

    def extract_functions_to_test(self) -> list[AFunction]:
        """Retrieve the functions names and implementations defined in the current cell"""
        # Only functions with names starting with `solution_` will be candidates for tests
        functions: dict[str, str] = {}
        tree = ast.parse(self.cell)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("solution_"):
                functions.update({str(node.name): ast.unparse(node)})

        return [
            AFunction(
                name=name.removeprefix("solution_"),
                implementation=function,
                source_code=functions[name],
            )
            for name, function in self.shell.user_ns.items()
            if name in functions
            and (callable(function) or inspect.iscoroutinefunction(function))
        ]

    def run_test_with_tracking(self, function: AFunction) -> IPytestResult:
        """Runs tests for a function while tracking execution count and handling threading"""
        assert isinstance(self.module_file, pathlib.Path)

        # Store execution count information for each cell
        cell_id = str(self.shell.parent_header["metadata"]["cellId"])  # type: ignore
        self.cell_execution_count[cell_id][function.name] += 1

        # Run the tests on a separate thread
        if self.threaded:
            assert isinstance(self.test_queue, Queue)
            thread = Thread(
                target=run_pytest_in_background,
                args=(
                    self.module_file,
                    function,
                    self.test_queue,
                ),
            )
            thread.start()
            thread.join()
            result = self.test_queue.get()
        else:
            result = run_pytest_for_function(self.module_file, function)

        match result.status:
            case IPytestOutcome.FINISHED:
                return dataclasses.replace(
                    result,
                    test_attempts=self.cell_execution_count[cell_id][function.name],
                )
            case _:
                return result

    def run_cell(self) -> list[IPytestResult]:
        """Evaluates the cell via IPython and runs tests for the functions"""
        try:
            result = self.shell.run_cell(self.cell, silent=True)  # type: ignore
            result.raise_error()
        except Exception as err:
            return [
                IPytestResult(
                    status=IPytestOutcome.COMPILE_ERROR,
                    exceptions=[err],
                    cell_content=self.cell,
                )
            ]

        functions_to_run = self.extract_functions_to_test()

        if not functions_to_run:
            return [
                IPytestResult(
                    status=IPytestOutcome.SOLUTION_FUNCTION_MISSING,
                    exceptions=[FunctionNotFoundError()],
                )
            ]

        # Run the tests for each function
        test_results = [
            self.run_test_with_tracking(function) for function in functions_to_run
        ]

        return test_results

    @contextmanager
    def traceback_handling(self, debug: bool):
        """Context manager to temporarily modify traceback behavior"""
        original_traceback = self.shell._showtraceback
        try:
            if not debug:
                self.shell._showtraceback = lambda *args, **kwargs: None
            yield
        finally:
            self.shell._showtraceback = original_traceback

    @cell_magic
    def ipytest(self, line: str, cell: str):
        """The `%%ipytest` cell magic"""
        # Check that the magic is called from a notebook
        if not self.shell:
            raise InstanceNotFoundError("InteractiveShell")

        # Store the cell content
        self.cell = cell

        # Parse arguments
        module_name, test_path, is_debug, is_async = self.parse_magic_args(line)

        # Store module_name and module_file
        self.module_name = module_name
        module_file = test_path / f"test_{module_name}.py"
        self.module_file = module_file

        # Check if we need to run the tests on a separate thread
        if is_async:
            self.threaded = True
            self.test_queue = Queue()

        with self.traceback_handling(is_debug):
            # Check that the test module file exists
            if not (self.module_file and self.module_file.exists()):
                raise FileNotFoundError(self.module_file)

            # Run the cell
            results = self.run_cell()

            # If in debug mode, display debug information first
            if is_debug:
                debug_output = DebugOutput(
                    module_name=self.module_name,
                    module_file=self.module_file,
                    results=results,
                )
                display(HTML(debug_output.to_html()))

            # Parse the AST of the test module to retrieve the solution code
            ast_parser = AstParser(self.module_file)

            # Display the test results and the solution code
            for result in results:
                solution = (
                    ast_parser.get_solution_code(result.function.name)
                    if result.function and result.function.name
                    else None
                )
                TestResultOutput(
                    result,
                    solution,
                    self.shell.openai_client,  # type: ignore
                ).display_results()


def load_ipython_extension(ipython):
    """
    Any module file that defines a function named `load_ipython_extension`
    can be loaded via `%load_ext module.path` or be configured to be
    autoloaded by IPython at startup time.
    """
    # Initialize OpenAI client based on AI support availability
    if HAS_AI_SUPPORT:
        # Configure the API key for the OpenAI client
        openai_env = find_dotenv("openai.env")
        if openai_env:
            load_dotenv(openai_env)

        api_key = os.getenv("OPENAI_API_KEY")
        model = os.getenv("OPENAI_MODEL")
        language = os.getenv("OPENAI_LANGUAGE")

        # First, validate the key
        if OpenAIWrapper is not None:  # Type guard
            key_validation = OpenAIWrapper.validate_api_key(api_key)
            if not key_validation.is_valid:
                message = key_validation.user_message
                message_color = "#ffebee"  # Red
                ipython.openai_client = None
            else:
                assert api_key is not None  # must be so at this point
                try:
                    openai_client, model_validation = OpenAIWrapper.create_validated(
                        api_key, model, language
                    )

                    if model_validation.is_valid:
                        ipython.openai_client = openai_client
                        message_color = "#d9ead3"  # Green
                    else:
                        message_color = "#ffebee"  # Red
                        ipython.openai_client = None

                    message = model_validation.user_message
                except OpenAIWrapperError as e:
                    ipython.openai_client = None
                    message = f"🚫 <strong style='color: red;'>OpenAI configuration error:</strong><br>{str(e)}"
                    message_color = "#ffebee"
                except Exception as e:
                    # Handle any other unexpected errors
                    ipython.openai_client = None
                    message = f"🚫 <strong style='color: red;'>Unexpected error:</strong><br>{str(e)}"
                    message_color = "#ffebee"
        else:
            # This should not happen if HAS_AI_SUPPORT is True, but safety first
            ipython.openai_client = None
            message = "🚫 <strong style='color: red;'>AI support initialization failed</strong>"
            message_color = "#ffebee"

        display(
            HTML(
                "<div style='background-color: "
                f"{message_color}; border-radius: 5px; padding: 10px;'>"
                f"{message}"
                "</div>"
            )
        )
    else:
        # AI support not available
        ipython.openai_client = None
        message = (
            "ℹ️ <strong>AI features disabled:</strong> Install with "
            "<code>pip install ipytestsuite[ai]</code> to enable AI-powered explanations."
        )
        message_color = "#e3f2fd"  # Light blue
        display(
            HTML(
                "<div style='background-color: "
                f"{message_color}; border-radius: 5px; padding: 10px;'>"
                f"{message}"
                "</div>"
            )
        )

    # Register the magic
    ipython.register_magics(TestMagic)

    ai_status = (
        "with AI support"
        if HAS_AI_SUPPORT
        and hasattr(ipython, "openai_client")
        and ipython.openai_client
        else "core features only"
    )
    message = (
        "<div style='background-color: #fffde7; border-radius: 5px; padding: 10px;'>"
        f"🔄 <strong>IPytest extension (re)loaded</strong> ({ai_status}).</div>"
    )
    display(HTML(message))
