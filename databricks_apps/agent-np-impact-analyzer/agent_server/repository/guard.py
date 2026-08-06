"""Validation and redaction helpers for repository content."""

import re
from pathlib import PurePosixPath

from agent_server.config import RepositoryConfig
from agent_server.repository.errors import RepositoryAccessError, RepositoryErrorCode

SENSITIVE_NAMES = frozenset(
    {
        ".env",
        ".env.local",
        "id_rsa",
        "id_dsa",
        "credentials",
        "credentials.json",
        "secrets.json",
        "token",
        "token.json",
        ".databrickscfg",
    }
)
SENSITIVE_SUFFIXES = frozenset({".pem", ".key", ".p12", ".pfx", ".crt", ".cer"})

_URI_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
_SENSITIVE_ASSIGNMENT = re.compile(
    r"(?im)^(\s*(?:api_key|access_token|client_secret|password|secret)\s*=\s*)"
    r"(?:\"[^\"\r\n]*\"|'[^'\r\n]*'|[^\s#\r\n]+)"
)
_PRIVATE_KEY_BLOCK = re.compile(
    r"-----BEGIN (?P<label>[A-Z ]*PRIVATE KEY)-----.*?-----END (?P=label)-----",
    re.DOTALL,
)


def _path_not_allowed() -> RepositoryAccessError:
    return RepositoryAccessError(
        RepositoryErrorCode.PATH_NOT_ALLOWED,
        "The requested repository path is not allowed.",
    )


def normalize_relative_path(candidate: str) -> str:
    """Return a normalized POSIX-relative path or raise a safe access error."""
    path = candidate.replace("\\", "/")
    if not path or path.startswith("/") or _URI_SCHEME.match(path):
        raise _path_not_allowed()

    parts = PurePosixPath(path).parts
    if not parts or any(part == ".." for part in parts):
        raise _path_not_allowed()

    normalized = str(PurePosixPath(*parts))
    if normalized in {"", "."}:
        raise _path_not_allowed()
    return normalized


def validate_file_policy(
    relative_path: str, size_bytes: int | None, config: RepositoryConfig
) -> str:
    """Ensure a repository file path and known size meet the read policy."""
    path = normalize_relative_path(relative_path)
    pure_path = PurePosixPath(path)
    segments = {segment.lower() for segment in pure_path.parts}
    basename = pure_path.name.lower()
    suffix = pure_path.suffix.lower()

    if ".git" in segments or basename in SENSITIVE_NAMES or suffix in SENSITIVE_SUFFIXES:
        raise RepositoryAccessError(
            RepositoryErrorCode.FILE_TYPE_NOT_ALLOWED,
            "The requested file type is not allowed.",
        )
    if suffix not in config.allowed_extensions:
        raise RepositoryAccessError(
            RepositoryErrorCode.FILE_TYPE_NOT_ALLOWED,
            "The requested file type is not allowed.",
        )
    if size_bytes is not None and size_bytes > config.max_file_bytes:
        raise RepositoryAccessError(
            RepositoryErrorCode.FILE_TOO_LARGE,
            "The requested file exceeds the maximum allowed size.",
        )
    return path


def redact_sensitive_content(content: str) -> tuple[str, bool]:
    """Redact configured assignment values and PEM private keys from text."""
    sanitized, assignment_count = _SENSITIVE_ASSIGNMENT.subn(r"\1[REDACTED]", content)
    sanitized, key_count = _PRIVATE_KEY_BLOCK.subn("[REDACTED PRIVATE KEY]", sanitized)
    return sanitized, bool(assignment_count or key_count)
