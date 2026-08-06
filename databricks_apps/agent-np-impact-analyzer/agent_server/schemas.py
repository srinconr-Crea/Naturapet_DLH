"""Shared schemas for repository access and impact analysis."""

from typing import Protocol

from pydantic import BaseModel


class RepositoryContext(BaseModel):
    repo_id: int
    path: str
    url: str
    provider: str
    branch: str
    head_commit_id: str


class RepositoryEntry(BaseModel):
    relative_path: str
    object_type: str
    size_bytes: int | None = None


class RepositoryFile(BaseModel):
    relative_path: str
    content: str
    size_bytes: int
    truncated: bool = False
    redacted: bool = False


class RepositoryGateway(Protocol):
    def get_context(self) -> RepositoryContext:
        raise NotImplementedError

    def list_tree(
        self, relative_path: str = "", max_depth: int | None = None
    ) -> list[RepositoryEntry]:
        raise NotImplementedError

    def read_file(self, relative_path: str) -> RepositoryFile:
        raise NotImplementedError
