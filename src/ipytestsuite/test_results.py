import html
from dataclasses import dataclass
from types import TracebackType

from .models import TestOutcome
from .utilities import strip_ansi_codes


@dataclass
class TestCaseResult:
    """Container class to store the test results when we collect them"""

    test_name: str
    outcome: TestOutcome
    exception: BaseException | None = None
    traceback: TracebackType | None = None
    formatted_exception: str = ""
    stdout: str = ""
    stderr: str = ""
    report_output: str = ""

    def __str__(self) -> str:
        """Basic string representation"""
        return (
            f"TestCaseResult(\n"
            f"  test_name: {self.test_name}\n"
            f"  outcome: {self.outcome.name if self.outcome else 'None'}\n"
            f"  exception: {type(self.exception).__name__ if self.exception else 'None'}"
            f" - {str(self.exception) if self.exception else ''}\n"
            f"  formatted_exception: {self.formatted_exception[:100]}..."
            f" ({len(self.formatted_exception)} chars)\n"
            f"  stdout: {len(self.stdout)} chars\n"
            f"  stderr: {len(self.stderr)} chars\n"
            f"  report_output: {len(self.report_output)} chars\n"
            ")"
        )

    def to_html(self) -> str:
        """HTML representation of the test result"""
        # CSS styles for the output
        styles = """
        <style>
            .test-result {
                font-family: system-ui, -apple-system, sans-serif;
                margin: 0.75rem 0;
                padding: 1rem;
                border-radius: 0.5rem;
                transition: all 0.2s ease;
            }
            .test-header {
                display: flex;
                align-items: center;
                gap: 0.75rem;
                margin-bottom: 0.75rem;
            }
            .test-icon {
                font-size: 1.25rem;
                width: 1.5rem;
                height: 1.5rem;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .test-name {
                font-family: ui-monospace, monospace;
                font-size: 0.9rem;
                padding: 0.25rem 0.5rem;
                background: rgba(0, 0, 0, 0.05);
                border-radius: 0.25rem;
            }
            .test-status {
                font-weight: 600;
                font-size: 1rem;
            }
            .test-pass {
                background-color: #f0fdf4;
                border: 1px solid #86efac;
            }
            .test-fail {
                background-color: #fef2f2;
                border: 1px solid #fecaca;
            }
            .test-error {
                background-color: #fff7ed;
                border: 1px solid #fed7aa;
            }
            .error-block {
                background-color: #ffffff;
                border: 1px solid rgba(0, 0, 0, 0.1);
                padding: 1rem;
                border-radius: 0.375rem;
                margin-top: 0.75rem;
            }
            .error-title {
                font-weight: 600;
                color: #dc2626;
                margin-bottom: 0.5rem;
            }
            .error-message {
                font-family: ui-monospace, monospace;
                font-size: 0.9rem;
                white-space: pre-wrap;
                margin: 0;
            }
            .output-section {
                margin-top: 0.75rem;
            }
            .output-tabs {
                display: flex;
                gap: 0.5rem;
                border-bottom: 1px solid #e5e7eb;
                margin-bottom: 0.5rem;
            }
            .output-tab {
                border: none;
                background: transparent;
                padding: 0.5rem 1rem;
                font-size: 0.9rem;
                cursor: pointer;
                border-bottom: 2px solid transparent;
                color: #6b7280;
            }
            .output-tab.active {
                border-bottom-color: #3b82f6;
                color: #1f2937;
                font-weight: 500;
            }
            .output-content {
                padding: 1rem;
                background: #ffffff;
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 0.375rem;
            }
            .output-pane {
                display: none;
            }
            .output-pane.active {
                display: block;
            }
        </style>
        """

        # Determine test status and icon
        match self.outcome:
            case TestOutcome.PASS:
                status_class = "test-pass"
                icon = "✅"
                status_text = "Passed"
            case TestOutcome.FAIL:
                status_class = "test-fail"
                icon = "❌"
                status_text = "Failed"
            case TestOutcome.TEST_ERROR:
                status_class = "test-error"
                icon = "🚨"
                status_text = "Syntax Error"
            case _:
                status_class = "test-error"
                icon = "⚠️"
                status_text = "Error"

        # Start building the HTML content
        test_name = self.test_name.split("::")[-1]
        html_parts = [styles]

        # Main container
        html_parts.append(
            f"""
        <div class="test-result {status_class}">
            <div class="test-header">
                <span class="test-icon">{icon}</span>
                {f'<span class="test-name">{html.escape(test_name)}</span>' if test_name else ""}
                <span class="test-status">{html.escape(status_text)}</span>
            </div>
        """
        )

        # Exception information if test failed
        if self.exception is not None:
            exception_type = type(self.exception).__name__
            exception_message = strip_ansi_codes(str(self.exception))

            html_parts.append(
                f"""
            <div class="error-block">
                <div class="error-title">{html.escape(exception_type)}</div>
                <pre class="error-message">{html.escape(exception_message)}</pre>
            </div>
            """
            )

        # Output sections (if any)
        if self.stdout or self.stderr:
            # Generate unique IDs for this test's tabs
            tab_id = f"test_{hash(self.test_name)}"
            html_parts.append(
                f"""
                        <div id="{tab_id}_container" class="output-section">
                            <div class="output-tabs">
                                <button class="output-tab active"
                                        onclick="
                                            document.querySelectorAll('#{tab_id}_container .output-tab').forEach(t => t.classList.remove('active'));
                                            document.querySelectorAll('#{tab_id}_container .output-pane').forEach(p => p.classList.remove('active'));
                                            this.classList.add('active');
                                            document.querySelector('#{tab_id}_output').classList.add('active');"
                                >Output</button>
                                <button class="output-tab"
                                        onclick="
                                            document.querySelectorAll('#{tab_id}_container .output-tab').forEach(t => t.classList.remove('active'));
                                            document.querySelectorAll('#{tab_id}_container .output-pane').forEach(p => p.classList.remove('active'));
                                            this.classList.add('active');
                                            document.querySelector('#{tab_id}_error').classList.add('active');"
                                >Error</button>
                            </div>
                            <div class="output-content">
                                <div id="{tab_id}_output" class="output-pane active">
                                    <pre>{html.escape(strip_ansi_codes(self.stdout)) if self.stdout else "No output"}</pre>
                                </div>
                                <div id="{tab_id}_error" class="output-pane">
                                    <pre>{html.escape(strip_ansi_codes(self.stderr)) if self.stderr else "No errors"}</pre>
                                </div>
                            </div>
                        </div>
                        """
            )

        # Close main div
        html_parts.append("</div>")

        return "\n".join(html_parts)
