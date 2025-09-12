from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

import ipywidgets
from IPython.display import Code, display as ipython_display
from ipywidgets import HTML

from .models import IPytestOutcome, IPytestResult, TestOutcome
from .test_results import TestCaseResult

if TYPE_CHECKING:
    from .ai_helpers import AIExplanation, OpenAIWrapper

# Try to import AI-related classes
try:
    from .ai_helpers import AIExplanation, OpenAIWrapper

    HAS_AI_SUPPORT = True
except ImportError:
    HAS_AI_SUPPORT = False
    AIExplanation = None
    OpenAIWrapper = None


@dataclass
class DebugOutput:
    """Class to format debug information about test execution"""

    module_name: str
    module_file: Path
    results: list[IPytestResult]

    def to_html(self) -> str:
        """Format debug information as HTML"""
        debug_parts = [
            """
            <style>
                .debug-container {
                    font-family: ui-monospace, monospace;
                    background: #f8f9fa;
                    padding: 1rem;
                    border-radius: 0.5rem;
                    margin: 1rem 0;
                }
                .debug-title {
                    font-size: 1.2rem;
                    font-weight: 600;
                    margin-bottom: 1rem;
                }
                .debug-section {
                    margin: 0.5rem 0;
                }
                .debug-result {
                    margin: 1rem 0;
                    padding: 0.5rem;
                    border: 1px solid #e5e7eb;
                    border-radius: 0.375rem;
                }
                .debug-list {
                    margin-left: 1rem;
                }
            </style>
            <div class="debug-container">
        """
        ]

        # Overall test run info
        debug_parts.append('<div class="debug-title">Debug Information</div>')
        debug_parts.append(
            '<div class="debug-section">'
            f"Module: {self.module_name}<br>"
            f"Module file: {self.module_file}<br>"
            f"Number of results: {len(self.results)}"
            "</div>"
        )

        # Detailed results
        for i, result in enumerate(self.results, 1):
            debug_parts.append(
                f'<div class="debug-result">'
                f"<strong>Result #{i}</strong><br>"
                f"Status: {result.status.name if result.status else 'None'}<br>"
                f"Function: {result.function.name if result.function else 'None'}<br>"
                f"Solution attempts: {result.test_attempts}"
            )

            if result.test_results:
                debug_parts.append(
                    f'<div class="debug-section">'
                    f"Test Results ({len(result.test_results)}):"
                    '<div class="debug-list">'
                )
                for test in result.test_results:
                    debug_parts.append(
                        f"• {test.test_name}: {test.outcome.name}"
                        f"{f' - {type(test.exception).__name__}: {str(test.exception)}' if test.exception else ''}<br>"
                    )
                debug_parts.append("</div></div>")

            if result.exceptions:
                debug_parts.append(
                    f'<div class="debug-section">'
                    f"Exceptions ({len(result.exceptions)}):"
                    '<div class="debug-list">'
                )
                for exc in result.exceptions:
                    debug_parts.append(f"• {type(exc).__name__}: {str(exc)}<br>")
                debug_parts.append("</div></div>")

            debug_parts.append("</div>")

        debug_parts.append("</div>")

        return "\n".join(debug_parts)


@dataclass
class TestResultOutput:
    """Class to prepare and display test results in a Jupyter notebook"""

    ipytest_result: IPytestResult
    solution: str | None = None
    MAX_ATTEMPTS: ClassVar[int] = 3
    openai_client: "OpenAIWrapper | None" = None

    def display_results(self) -> None:
        """Display the test results in an output widget as a VBox"""
        cells = []

        output_cell = self.prepare_output_cell()
        solution_cell = self.prepare_solution_cell()

        cells.append(output_cell)

        tests_finished = self.ipytest_result.status == IPytestOutcome.FINISHED
        success = (
            all(
                test.outcome == TestOutcome.PASS
                for test in self.ipytest_result.test_results
            )
            if self.ipytest_result.test_results
            else False
        )

        if success or self.ipytest_result.test_attempts >= self.MAX_ATTEMPTS:
            cells.append(solution_cell)
        else:
            if tests_finished:
                attempts_remaining = (
                    self.MAX_ATTEMPTS - self.ipytest_result.test_attempts
                )
                cells.append(
                    HTML(
                        '<div style="margin-top: 1.5rem; font-family: system-ui, -apple-system, sans-serif;">'
                        f'<div style="display: flex; align-items: center; gap: 0.5rem;">'
                        '<span style="font-size: 1.2rem;">📝</span>'
                        '<span style="font-size: 1.1rem; font-weight: 500;">Solution will be available after '
                        f"{attempts_remaining} more failed attempt{'s' if attempts_remaining > 1 else ''}</span>"
                        "</div>"
                        "</div>"
                    )
                )

        ipython_display(
            ipywidgets.VBox(
                children=cells,
                layout={
                    "border": "1px solid #e5e7eb",
                    "background-color": "#ffffff",
                    "margin": "5px",
                    "padding": "0.75rem",
                    "border-radius": "0.5rem",
                },
            )
        )

    def prepare_solution_cell(self) -> ipywidgets.Widget:
        """Prepare the cell to display the solution code with a collapsible accordion"""
        # Return an empty output widget if no solution is provided
        if self.solution is None:
            return ipywidgets.Output()

        # Create the solution content
        solution_output = ipywidgets.Output(
            layout=ipywidgets.Layout(padding="1rem", border="1px solid #e5e7eb")
        )
        with solution_output:
            ipython_display(Code(data=self.solution, language="python"))

        # Create header with emoji
        header_output = ipywidgets.Output()
        with header_output:
            ipython_display(
                HTML(
                    '<div style="display: flex; align-items: center; gap: 0.5rem;">'
                    '<span style="font-size: 1.1rem;">👉</span>'
                    '<span style="font-size: 1.1rem; font-weight: 500;">Proposed solution</span>'
                    "</div>"
                )
            )

        # Create the collapsible accordion (closed by default)
        accordion = ipywidgets.Accordion(
            children=[solution_output],
            selected_index=None,  # Start collapsed
            titles=("View solution",),
            layout=ipywidgets.Layout(
                margin="1.5rem 0 0 0",
                border="1px solid #e5e7eb",
                border_radius="0.5rem",
            ),
        )

        return ipywidgets.VBox(
            children=[header_output, accordion],
            layout=ipywidgets.Layout(
                margin="0",
                padding="0",
            ),
        )

    def prepare_output_cell(self) -> ipywidgets.Output:
        """Prepare the cell to display the test results"""
        output_cell = ipywidgets.Output()

        # Header with test function name
        function = self.ipytest_result.function
        title = "Test Results for " if function else "Test Results "
        output_cell.append_display_data(
            HTML(
                '<div style="overflow: hidden;">'
                f'<h2 style="font-size: 1.5rem; margin: 0;">{title}'
                '<code style="font-size: 1.1rem; background: #f3f4f6; padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-family: ui-monospace, monospace;">'
                f"solution_{function.name}</code></h2>"
                if function is not None
                else f'<h2 style="font-size: 1.5rem; margin: 0;">{title}</h2></div>'
            )
        )

        match self.ipytest_result.status:
            case (
                IPytestOutcome.COMPILE_ERROR
                | IPytestOutcome.PYTEST_ERROR
                | IPytestOutcome.UNKNOWN_ERROR
            ):
                # We know that there is exactly one exception
                assert self.ipytest_result.exceptions is not None
                # We know that there is no test results
                assert self.ipytest_result.test_results is None

                exception = self.ipytest_result.exceptions[0]

                # Create a TestCaseResult for consistency
                error_result = TestCaseResult(
                    test_name=f"error::solution_{function.name}" if function else "::",
                    outcome=TestOutcome.TEST_ERROR,
                    exception=exception,
                )

                output_cell.append_display_data(HTML(error_result.to_html()))

                if self.openai_client and HAS_AI_SUPPORT and AIExplanation:
                    ai_explains = AIExplanation(
                        ipytest_result=self.ipytest_result,
                        exception=exception,
                        openai_client=self.openai_client,
                    )

                    output_cell.append_display_data(ai_explains.render())

            case IPytestOutcome.FINISHED if self.ipytest_result.test_results:
                # Calculate test statistics
                total_tests = len(self.ipytest_result.test_results)
                passed_tests = sum(
                    1
                    for test in self.ipytest_result.test_results
                    if test.outcome == TestOutcome.PASS
                )
                failed_tests = total_tests - passed_tests

                # Display summary
                output_cell.append_display_data(
                    HTML(
                        '<div style="margin-bottom: 1rem; font-size: 0.95rem;">'
                        f'<div style="color: #059669; margin-bottom: 0.25rem;">'
                        f"✅ {passed_tests}/{total_tests} tests passed</div>"
                        f'<div style="color: #dc2626;">'
                        f"❌ {failed_tests}/{total_tests} tests failed</div>"
                        "</div>"
                    )
                )

                # Display individual test results
                for test in self.ipytest_result.test_results:
                    output_cell.append_display_data(HTML(test.to_html()))

                failed_tests = [
                    test
                    for test in self.ipytest_result.test_results
                    if test.outcome != TestOutcome.PASS
                ]

                if (
                    self.openai_client
                    and failed_tests
                    and HAS_AI_SUPPORT
                    and AIExplanation
                ):
                    ai_explains = AIExplanation(
                        ipytest_result=self.ipytest_result,
                        exception=failed_tests[0].exception,
                        openai_client=self.openai_client,
                    )

                    output_cell.append_display_data(ai_explains.render())

            case IPytestOutcome.SOLUTION_FUNCTION_MISSING:
                output_cell.append_display_data(
                    HTML(
                        '<div class="test-result test-error" style="margin-top: 1rem;">'
                        '<div class="error-title">Solution Function Missing</div>'
                        "<p>Please implement the required solution function.</p>"
                        "</div>"
                    )
                )

            case IPytestOutcome.NO_TEST_FOUND:
                output_cell.append_display_data(HTML("<h3>No Test Found</h3>"))

        return output_cell
