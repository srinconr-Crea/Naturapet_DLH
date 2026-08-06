"""Read-only Databricks SDK client for the fixed Naturapet Git folder."""

from collections import deque
from pathlib import PurePosixPath
from typing import Any

from databricks.sdk.service.workspace import ExportFormat

from agent_server.config import RepositoryConfig
from agent_server.repository.errors import RepositoryAccessError, RepositoryErrorCode
from agent_server.repository.guard import (
    normalize_relative_path,
    redact_sensitive_content,
    validate_file_policy,
)
from agent_server.schemas import (
    RepositoryContext,
    RepositoryEntry,
    RepositoryFile,
    RepositoryTreeResult,
)


class DatabricksRepositoryClient:
    """Expose bounded, read-only repository operations through WorkspaceClient."""

    def __init__(self, workspace_client: Any, config: RepositoryConfig):
        self.workspace_client = workspace_client
        self.config = config

    def get_context(self) -> RepositoryContext:
        """Return the configured repository context after exact SDK validation."""
        try:
            repository = self.workspace_client.repos.get(self.config.repo_id)
        except Exception as error:
            raise self._read_error() from error

        path = self._normalize_repository_path(getattr(repository, "path", None))
        context_matches = (
            getattr(repository, "id", None) == self.config.repo_id
            and path == self.config.root
            and getattr(repository, "url", None) == self.config.url
            and getattr(repository, "provider", None) == self.config.provider
        )
        branch_matches = getattr(repository, "branch", None) == self.config.branch
        if not context_matches:
            raise RepositoryAccessError(
                RepositoryErrorCode.REPOSITORY_CONTEXT_MISMATCH,
                "The configured repository context does not match the requested repository.",
            )
        if not branch_matches:
            raise RepositoryAccessError(
                RepositoryErrorCode.BRANCH_NOT_ALLOWED,
                "The configured repository branch is not allowed.",
            )

        try:
            return RepositoryContext(
                repo_id=repository.id,
                path=path,
                url=repository.url,
                provider=repository.provider,
                branch=repository.branch,
                head_commit_id=repository.head_commit_id,
            )
        except Exception as error:
            raise self._read_error() from error

    def list_tree(
        self, relative_path: str = "", max_depth: int | None = None
    ) -> list[RepositoryEntry]:
        """List allowed files while preserving the public repository gateway contract."""
        return self.list_tree_result(relative_path, max_depth).entries

    def list_tree_result(
        self, relative_path: str = "", max_depth: int | None = None
    ) -> RepositoryTreeResult:
        """List allowed files and report whether bounded traversal omitted work."""
        normalized_start = self._validate_directory_path(relative_path)
        depth_limit = self.config.max_depth if max_depth is None else min(
            max_depth, self.config.max_depth
        )
        if depth_limit < 0:
            raise RepositoryAccessError(
                RepositoryErrorCode.PATH_NOT_ALLOWED,
                "The requested repository path is not allowed.",
            )

        start_path = self._absolute_path(normalized_start)
        pending = deque([(start_path, 0)])
        entries: list[RepositoryEntry] = []
        visited_directories = 0
        visited_candidates = 0
        limit_reached = False

        while pending:
            if visited_directories >= self.config.max_files:
                limit_reached = True
                break
            current_path, depth = pending.popleft()
            visited_directories += 1
            try:
                children = self.workspace_client.workspace.list(current_path)
                for child in children:
                    if visited_candidates >= self.config.max_files:
                        limit_reached = True
                        break
                    visited_candidates += 1
                    child_path = str(getattr(child, "path", ""))
                    object_type = self._object_type(child)
                    if object_type == "DIRECTORY":
                        if depth < depth_limit:
                            try:
                                child_relative = self._relative_path(child_path)
                                child_relative = self._validate_directory_path(child_relative)
                            except RepositoryAccessError:
                                continue
                            pending.append((self._absolute_path(child_relative), depth + 1))
                        continue
                    if object_type != "FILE":
                        continue
                    relative = self._relative_path(child_path)
                    try:
                        relative = validate_file_policy(
                            relative, getattr(child, "size", None), self.config
                        )
                    except RepositoryAccessError:
                        continue
                    entries.append(
                        RepositoryEntry(
                            relative_path=relative,
                            object_type=object_type,
                            size_bytes=getattr(child, "size", None),
                        )
                    )
            except RepositoryAccessError:
                raise
            except Exception as error:
                raise self._read_error() from error

        return RepositoryTreeResult(entries=entries, limit_reached=limit_reached)

    def read_file(self, relative_path: str) -> RepositoryFile:
        """Read one allowed UTF-8 file, bounded by policy and redacted in memory."""
        normalized = validate_file_policy(relative_path, None, self.config)
        absolute_path = self._absolute_path(normalized)
        try:
            status = self.workspace_client.workspace.get_status(absolute_path)
            reported_size = getattr(status, "size", None)
            normalized = validate_file_policy(normalized, reported_size, self.config)
            if self._object_type(status) != "FILE":
                raise RepositoryAccessError(
                    RepositoryErrorCode.FILE_TYPE_NOT_ALLOWED,
                    "The requested file type is not allowed.",
                )
            with self.workspace_client.workspace.download(
                absolute_path, format=ExportFormat.AUTO
            ) as stream:
                raw = stream.read(self.config.max_file_bytes + 1)
        except RepositoryAccessError:
            raise
        except Exception as error:
            raise self._read_error() from error

        if len(raw) > self.config.max_file_bytes:
            raise RepositoryAccessError(
                RepositoryErrorCode.FILE_TOO_LARGE,
                "The requested file exceeds the maximum allowed size.",
            )
        try:
            content = raw.decode("utf-8")
        except UnicodeDecodeError as error:
            raise RepositoryAccessError(
                RepositoryErrorCode.CONTENT_REDACTED,
                "The requested file cannot be read as UTF-8 text.",
            ) from error
        content, redacted = redact_sensitive_content(content)
        return RepositoryFile(
            relative_path=normalized,
            content=content,
            size_bytes=reported_size if reported_size is not None else len(raw),
            redacted=redacted,
        )

    def _absolute_path(self, relative_path: str) -> str:
        return str(PurePosixPath(self.config.root, relative_path))

    def _normalize_repository_path(self, path: Any) -> str | None:
        if not isinstance(path, str):
            return None
        if path.startswith("/Naturapet_BI/"):
            return f"/Workspace{path}"
        return path

    def _relative_path(self, absolute_path: str) -> str:
        try:
            return str(PurePosixPath(absolute_path).relative_to(PurePosixPath(self.config.root)))
        except ValueError as error:
            raise RepositoryAccessError(
                RepositoryErrorCode.PATH_NOT_ALLOWED,
                "The requested repository path is not allowed.",
            ) from error

    def _validate_directory_path(self, relative_path: str) -> str:
        if not relative_path:
            return ""
        normalized = normalize_relative_path(relative_path)
        if ".git" in {part.lower() for part in PurePosixPath(normalized).parts}:
            raise RepositoryAccessError(
                RepositoryErrorCode.FILE_TYPE_NOT_ALLOWED,
                "The requested file type is not allowed.",
            )
        return normalized

    def _object_type(self, entry: Any) -> str:
        value = getattr(entry, "object_type", "")
        return str(getattr(value, "value", value)).upper()

    def _read_error(self) -> RepositoryAccessError:
        return RepositoryAccessError(
            RepositoryErrorCode.DATABRICKS_READ_ERROR,
            "No fue posible completar la lectura solicitada.",
        )
