"""Safe error types for repository access."""

from enum import StrEnum


class RepositoryErrorCode(StrEnum):
    REPOSITORY_CONTEXT_MISMATCH = "REPOSITORY_CONTEXT_MISMATCH"
    BRANCH_NOT_ALLOWED = "BRANCH_NOT_ALLOWED"
    PATH_NOT_ALLOWED = "PATH_NOT_ALLOWED"
    FILE_TYPE_NOT_ALLOWED = "FILE_TYPE_NOT_ALLOWED"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    CONTENT_REDACTED = "CONTENT_REDACTED"
    SEARCH_LIMIT_REACHED = "SEARCH_LIMIT_REACHED"
    DATABRICKS_READ_ERROR = "DATABRICKS_READ_ERROR"


class RepositoryAccessError(RuntimeError):
    def __init__(self, code: RepositoryErrorCode, safe_message: str):
        super().__init__(safe_message)
        self.code = code
        self.safe_message = safe_message
