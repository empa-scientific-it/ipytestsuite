from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .results import TestCaseResult


class TestOutcome(Enum):
    PASS = 1
    FAIL = 2
    TEST_ERROR = 3


class IPytestOutcome(Enum):
    FINISHED = 0
    COMPILE_ERROR = 1
    SOLUTION_FUNCTION_MISSING = 2
    NO_TEST_FOUND = 3
    PYTEST_ERROR = 4
    UNKNOWN_ERROR = 5


@dataclass
class AFunction:
    """Container class to store a function and its metadata"""

    name: str
    implementation: Callable[..., Any]
    source_code: str | None


@dataclass
class IPytestResult:
    """Class to store the results of running pytest on a solution function"""

    function: AFunction | None = None
    status: IPytestOutcome | None = None
    test_results: list["TestCaseResult"] | None = None
    exceptions: list[BaseException] | None = None
    test_attempts: int = 0
    cell_content: str | None = None
