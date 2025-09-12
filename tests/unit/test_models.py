"""
Unit tests for ipytestsuite.models module
"""

from ipytestsuite.models import AFunction, IPytestOutcome, IPytestResult, TestOutcome


class TestTestOutcome:
    """Test TestOutcome enum"""

    def test_enum_values(self):
        """Test that TestOutcome has expected values"""
        assert TestOutcome.PASS.value == 1
        assert TestOutcome.FAIL.value == 2
        assert TestOutcome.TEST_ERROR.value == 3

    def test_enum_names(self):
        """Test that TestOutcome has expected names"""
        assert TestOutcome.PASS.name == "PASS"
        assert TestOutcome.FAIL.name == "FAIL"
        assert TestOutcome.TEST_ERROR.name == "TEST_ERROR"


class TestIPytestOutcome:
    """Test IPytestOutcome enum"""

    def test_enum_values(self):
        """Test that IPytestOutcome has expected values"""
        assert IPytestOutcome.FINISHED.value == 0
        assert IPytestOutcome.COMPILE_ERROR.value == 1
        assert IPytestOutcome.SOLUTION_FUNCTION_MISSING.value == 2
        assert IPytestOutcome.NO_TEST_FOUND.value == 3
        assert IPytestOutcome.PYTEST_ERROR.value == 4
        assert IPytestOutcome.UNKNOWN_ERROR.value == 5

    def test_enum_names(self):
        """Test that IPytestOutcome has expected names"""
        assert IPytestOutcome.FINISHED.name == "FINISHED"
        assert IPytestOutcome.COMPILE_ERROR.name == "COMPILE_ERROR"
        assert (
            IPytestOutcome.SOLUTION_FUNCTION_MISSING.name == "SOLUTION_FUNCTION_MISSING"
        )
        assert IPytestOutcome.NO_TEST_FOUND.name == "NO_TEST_FOUND"
        assert IPytestOutcome.PYTEST_ERROR.name == "PYTEST_ERROR"
        assert IPytestOutcome.UNKNOWN_ERROR.name == "UNKNOWN_ERROR"


class TestAFunction:
    """Test AFunction dataclass"""

    def test_creation_with_all_fields(self):
        """Test creating AFunction with all fields"""

        def sample_func(x):
            return x * 2

        source = "def sample_func(x):\n    return x * 2"

        func = AFunction(
            name="sample_func", implementation=sample_func, source_code=source
        )

        assert func.name == "sample_func"
        assert func.implementation == sample_func
        assert func.source_code == source

    def test_creation_with_none_source(self):
        """Test creating AFunction with None source_code"""

        def sample_func(x):
            return x * 2

        func = AFunction(
            name="sample_func", implementation=sample_func, source_code=None
        )

        assert func.name == "sample_func"
        assert func.implementation == sample_func
        assert func.source_code is None

    def test_callable_implementation(self):
        """Test that implementation is actually callable"""

        def add_func(a, b):
            return a + b

        func = AFunction(
            name="add_func",
            implementation=add_func,
            source_code="def add_func(a, b): return a + b",
        )

        # Test that the implementation works
        assert func.implementation(3, 4) == 7

    def test_lambda_implementation(self):
        """Test AFunction with lambda implementation"""

        func = AFunction(
            name="square", implementation=lambda x: x**2, source_code="lambda x: x ** 2"
        )

        assert func.implementation(5) == 25


class TestIPytestResult:
    """Test IPytestResult dataclass"""

    def test_creation_with_defaults(self):
        """Test creating IPytestResult with default values"""
        result = IPytestResult()

        assert result.function is None
        assert result.status is None
        assert result.test_results is None
        assert result.exceptions is None
        assert result.test_attempts == 0
        assert result.cell_content is None

    def test_creation_with_function(self, sample_function):
        """Test creating IPytestResult with AFunction"""
        result = IPytestResult(
            function=sample_function, status=IPytestOutcome.FINISHED, test_attempts=1
        )

        assert result.function == sample_function
        assert result.status == IPytestOutcome.FINISHED
        assert result.test_attempts == 1
        assert result.test_results is None
        assert result.exceptions is None
        assert result.cell_content is None

    def test_creation_with_test_results(self, sample_function, sample_test_case_result):
        """Test creating IPytestResult with test results"""
        result = IPytestResult(
            function=sample_function,
            status=IPytestOutcome.FINISHED,
            test_results=[sample_test_case_result],
            test_attempts=2,
        )

        assert result.function == sample_function
        assert result.status == IPytestOutcome.FINISHED
        assert result.test_results is not None
        assert len(result.test_results) == 1
        assert result.test_results[0] == sample_test_case_result
        assert result.test_attempts == 2

    def test_creation_with_exceptions(self):
        """Test creating IPytestResult with exceptions"""
        exc = ValueError("Test error")

        result = IPytestResult(
            status=IPytestOutcome.PYTEST_ERROR,
            exceptions=[exc],
            cell_content="def bad_func(): raise ValueError('Test error')",
        )

        assert result.status == IPytestOutcome.PYTEST_ERROR
        assert result.exceptions is not None
        assert len(result.exceptions) == 1
        assert result.exceptions[0] == exc
        assert (
            result.cell_content is not None and "def bad_func()" in result.cell_content
        )

    def test_multiple_exceptions(self):
        """Test IPytestResult with multiple exceptions"""
        exc1 = ValueError("Error 1")
        exc2 = TypeError("Error 2")

        result = IPytestResult(
            status=IPytestOutcome.UNKNOWN_ERROR, exceptions=[exc1, exc2]
        )

        assert result.exceptions is not None
        assert len(result.exceptions) == 2
        assert exc1 in result.exceptions
        assert exc2 in result.exceptions
