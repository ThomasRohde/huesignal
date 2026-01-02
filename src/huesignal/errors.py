"""Error codes and custom exceptions for huesignal."""

# Exit codes
EXIT_SUCCESS = 0
EXIT_GENERAL_ERROR = 1
EXIT_AUTH_FAILURE = 2
EXIT_BRIDGE_UNREACHABLE = 3
EXIT_NO_LIGHTS_MATCHED = 4
EXIT_AMBIGUOUS_MATCH = 5
EXIT_NOT_FOUND = 6
EXIT_TIMEOUT = 7
EXIT_INVALID_ARGUMENT = 8


class HuesignalError(Exception):
    """Base exception for huesignal."""

    exit_code = EXIT_GENERAL_ERROR

    def __init__(self, message: str, exit_code: int = EXIT_GENERAL_ERROR):
        super().__init__(message)
        self.exit_code = exit_code


class AuthError(HuesignalError):
    """Authentication error."""

    exit_code = EXIT_AUTH_FAILURE


class BridgeUnreachableError(HuesignalError):
    """Bridge is unreachable."""

    exit_code = EXIT_BRIDGE_UNREACHABLE


class NoLightsMatchedError(HuesignalError):
    """No lights matched the criteria."""

    exit_code = EXIT_NO_LIGHTS_MATCHED


class AmbiguousMatchError(HuesignalError):
    """Ambiguous match - multiple candidates."""

    exit_code = EXIT_AMBIGUOUS_MATCH


class NotFoundError(HuesignalError):
    """Resource not found."""

    exit_code = EXIT_NOT_FOUND


class TimeoutError(HuesignalError):
    """Operation timed out."""

    exit_code = EXIT_TIMEOUT
