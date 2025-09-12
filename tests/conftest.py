"""
Shared test fixtures and utilities for ipytestsuite tests.
"""

import tempfile
from pathlib import Path
from typing import Callable

import pytest

from ipytestsuite.models import AFunction, TestOutcome
from ipytestsuite.results import TestCaseResult


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests"""
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)


@pytest.fixture
def sample_function() -> AFunction:
    """Create a sample AFunction for testing"""

    def add_numbers(a: int, b: int) -> int:
        return a + b

    return AFunction(
        name="add_numbers",
        implementation=add_numbers,
        source_code="def add_numbers(a: int, b: int) -> int:\n    return a + b",
    )


@pytest.fixture
def sample_callable() -> Callable[[int, int], int]:
    """Create a simple callable for testing"""

    def multiply(a: int, b: int) -> int:
        return a * b

    return multiply


@pytest.fixture
def sample_test_case_result() -> TestCaseResult:
    """Create a sample TestCaseResult for testing"""
    return TestCaseResult(
        test_name="test_module::test_add_numbers",
        outcome=TestOutcome.PASS,
    )


@pytest.fixture
def failing_test_case_result() -> TestCaseResult:
    """Create a failing TestCaseResult for testing"""
    exception = AssertionError("Expected 5, got 4")
    return TestCaseResult(
        test_name="test_module::test_subtract_numbers",
        outcome=TestOutcome.FAIL,
        exception=exception,
        formatted_exception="AssertionError: Expected 5, got 4",
        stdout="Debug: calling subtract_numbers(5, 1)",
        stderr="Warning: deprecated function",
    )


@pytest.fixture
def error_test_case_result() -> TestCaseResult:
    """Create an error TestCaseResult for testing"""
    exception = ValueError("Invalid input")
    return TestCaseResult(
        test_name="test_module::test_invalid_input",
        outcome=TestOutcome.TEST_ERROR,
        exception=exception,
        formatted_exception="ValueError: Invalid input",
    )
