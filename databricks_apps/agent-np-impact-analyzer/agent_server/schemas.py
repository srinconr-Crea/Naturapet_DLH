"""Shared schemas for repository access and impact analysis."""

from typing import Protocol

from pydantic import BaseModel, Field, RootModel


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


class SearchMatch(BaseModel):
    relative_path: str
    line_number: int
    excerpt: str


class SearchResult(BaseModel):
    query: str
    matches: list[SearchMatch]
    files_scanned: int
    limit_reached: bool = False
    warnings: list[str] = Field(default_factory=list)


class RepositoryTreeResult(BaseModel):
    """Bounded repository tree and whether traversal omitted known work."""

    entries: list[RepositoryEntry]
    limit_reached: bool = False


class RepositoryEntriesResult(RootModel[list[RepositoryEntry]]):
    """JSON-array response used by the public repository tree tool."""


class RepositoryGateway(Protocol):
    def get_context(self) -> RepositoryContext:
        raise NotImplementedError

    def list_tree(
        self, relative_path: str = "", max_depth: int | None = None
    ) -> list[RepositoryEntry]:
        raise NotImplementedError


class RepositorySearchGateway(RepositoryGateway, Protocol):
    """Repository gateway extension that reports bounded traversal status."""

    def list_tree_result(
        self, relative_path: str = "", max_depth: int | None = None
    ) -> RepositoryTreeResult:
        raise NotImplementedError

    def read_file(self, relative_path: str) -> RepositoryFile:
        raise NotImplementedError
