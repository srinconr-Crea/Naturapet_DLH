"""Shared schemas for repository access and impact analysis."""

from enum import StrEnum
from pathlib import PurePosixPath
from typing import Literal, Protocol
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, RootModel, field_validator, model_validator


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


class Decision(StrEnum):
    FEASIBLE = "feasible"
    FEASIBLE_WITH_CONDITIONS = "feasible_with_conditions"
    NOT_FEASIBLE = "not_feasible"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EvidenceKind(StrEnum):
    DIRECT = "direct"
    INFERENCE = "inference"


def _validate_relative_path(value: str) -> str:
    """Reject paths that could cite content outside the verified repository."""
    path = PurePosixPath(value)
    if (
        not value
        or path.is_absolute()
        or "\\" in value
        or ":" in value
        or any(part == ".." for part in path.parts)
        or not path.parts
    ):
        raise ValueError("relative path must stay inside the repository")
    return value


class ImpactAnalysisModel(BaseModel):
    """Base model that rejects uncontrolled fields in the Supervisor contract."""

    model_config = ConfigDict(extra="forbid")


class RiskAssessment(ImpactAnalysisModel):
    level: RiskLevel
    reasons: list[str] = Field(min_length=1)


class FileReference(ImpactAnalysisModel):
    relative_path: str
    reason: str

    _validate_path = field_validator("relative_path")(_validate_relative_path)


class EvidenceItem(ImpactAnalysisModel):
    relative_path: str
    line_start: int | None = Field(default=None, ge=1)
    line_end: int | None = Field(default=None, ge=1)
    excerpt: str = Field(max_length=500)
    finding: str
    kind: EvidenceKind

    _validate_path = field_validator("relative_path")(_validate_relative_path)

    @model_validator(mode="after")
    def line_range_is_ordered(self) -> "EvidenceItem":
        if (
            self.line_start is not None
            and self.line_end is not None
            and self.line_end < self.line_start
        ):
            raise ValueError("line_end must be greater than or equal to line_start")
        return self


class ImplementationStep(ImpactAnalysisModel):
    order: int = Field(ge=1)
    action: str
    files: list[str]

    @field_validator("files")
    @classmethod
    def files_are_relative(cls, files: list[str]) -> list[str]:
        return [_validate_relative_path(path) for path in files]


class ImpactAnalysisDraft(ImpactAnalysisModel):
    request_summary: str
    decision: Decision
    risk: RiskAssessment
    target_files: list[FileReference]
    related_files: list[FileReference]
    evidence: list[EvidenceItem]
    implementation_plan: list[ImplementationStep]
    acceptance_criteria: list[str]
    prohibited_actions: list[str]
    assumptions: list[str]
    warnings: list[str]

    @model_validator(mode="after")
    def requires_evidence_for_supported_decisions(self) -> "ImpactAnalysisDraft":
        if self.decision is not Decision.INSUFFICIENT_EVIDENCE and not self.evidence:
            raise ValueError("evidence is required unless decision is insufficient_evidence")
        return self


class ImpactAnalysisResult(ImpactAnalysisDraft):
    schema_version: Literal["1.0"]
    analysis_id: str
    status: Literal["completed"]
    repository_context: RepositoryContext
    human_report_markdown: str


def finalize_analysis(
    draft: ImpactAnalysisDraft, context: RepositoryContext
) -> ImpactAnalysisResult:
    """Add application-controlled fields and derive the human report from JSON data."""
    from agent_server.output_renderer import render_markdown

    provisional = ImpactAnalysisResult(
        schema_version="1.0",
        analysis_id=str(uuid4()),
        status="completed",
        repository_context=context,
        **draft.model_dump(),
        human_report_markdown="",
    )
    return provisional.model_copy(
        update={"human_report_markdown": render_markdown(provisional)}
    )
