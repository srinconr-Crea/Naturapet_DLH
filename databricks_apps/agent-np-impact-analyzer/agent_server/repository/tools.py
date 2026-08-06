"""Read-only, bounded repository tools for the impact analyzer."""

import json
from dataclasses import dataclass

from agents import RunContextWrapper, function_tool

from agent_server.config import RepositoryConfig
from agent_server.repository.errors import RepositoryAccessError
from agent_server.schemas import (
    RepositoryContext,
    RepositoryEntriesResult,
    RepositoryFile,
    RepositoryGateway,
    RepositorySearchGateway,
    SearchMatch,
    SearchResult,
)


@dataclass(frozen=True)
class AnalysisRunContext:
    """Dependencies made available to read-only repository tools for one run."""

    repository: RepositoryGateway
    config: RepositoryConfig


def safe_tool_error(
    _context: RunContextWrapper[AnalysisRunContext], error: Exception
) -> str:
    """Return a non-sensitive error payload that the model can safely consume."""
    if isinstance(error, RepositoryAccessError):
        return json.dumps(
            {"error": {"code": error.code, "message": error.safe_message}}
        )
    return json.dumps(
        {
            "error": {
                "code": "DATABRICKS_READ_ERROR",
                "message": "No fue posible completar la lectura solicitada.",
            }
        }
    )


def search_text(
    repository: RepositorySearchGateway,
    config: RepositoryConfig,
    query: str,
    relative_path: str = "",
) -> SearchResult:
    """Find case-insensitive, line-bounded evidence in allowed repository files."""
    if not query.strip():
        raise ValueError("query must not be empty")
    if len(query) > 200:
        raise ValueError("query must not exceed 200 characters")

    normalized_query = query.casefold()
    matches: list[SearchMatch] = []
    tree = repository.list_tree_result(relative_path)
    file_entries = [
        entry
        for entry in tree.entries
        if entry.object_type.upper() == "FILE"
    ]
    files_truncated = tree.limit_reached
    per_file_truncated = False
    global_results_truncated = False
    files_scanned = 0

    for entry_index, entry in enumerate(file_entries):
        if len(matches) >= config.max_results:
            break

        file_matches = 0
        reached_global_limit = False
        if normalized_query in entry.relative_path.casefold():
            if file_matches >= config.max_results_per_file:
                per_file_truncated = True
            else:
                matches.append(
                    SearchMatch(
                        relative_path=entry.relative_path,
                        line_number=1,
                        excerpt=entry.relative_path[: config.max_excerpt_chars],
                    )
                )
                file_matches += 1
                reached_global_limit = len(matches) >= config.max_results

        if reached_global_limit and entry_index < len(file_entries) - 1:
            global_results_truncated = True
            break

        repository_file = repository.read_file(entry.relative_path)
        files_scanned += 1
        for line_number, line in enumerate(repository_file.content.splitlines(), start=1):
            if normalized_query not in line.casefold():
                continue
            if reached_global_limit:
                global_results_truncated = True
                break
            if file_matches >= config.max_results_per_file:
                per_file_truncated = True
                break
            matches.append(
                SearchMatch(
                    relative_path=repository_file.relative_path,
                    line_number=line_number,
                    excerpt=line[: config.max_excerpt_chars],
                )
            )
            file_matches += 1
            reached_global_limit = len(matches) >= config.max_results

        if global_results_truncated or reached_global_limit:
            break

    limit_reached = (
        files_truncated or per_file_truncated or global_results_truncated
    )
    return SearchResult(
        query=query,
        matches=matches,
        files_scanned=files_scanned,
        limit_reached=limit_reached,
        warnings=["SEARCH_LIMIT_REACHED"] if limit_reached else [],
    )


@function_tool(failure_error_function=safe_tool_error)
def get_repository_context(
    wrapper: RunContextWrapper[AnalysisRunContext],
) -> str:
    """Return the verified fixed repository context for the current analysis."""
    return wrapper.context.repository.get_context().model_dump_json()


@function_tool(failure_error_function=safe_tool_error)
def list_repository_tree(
    wrapper: RunContextWrapper[AnalysisRunContext],
    relative_path: str = "",
    max_depth: int | None = None,
) -> str:
    """List allowed repository file metadata inside a bounded relative path."""
    entries = wrapper.context.repository.list_tree(
        relative_path, max_depth
    )
    return RepositoryEntriesResult(entries).model_dump_json()


@function_tool(failure_error_function=safe_tool_error)
def read_repository_file(
    wrapper: RunContextWrapper[AnalysisRunContext], relative_path: str
) -> str:
    """Read one allowed repository text file after the repository policy validates it."""
    repository_file: RepositoryFile = wrapper.context.repository.read_file(relative_path)
    return repository_file.model_dump_json()


@function_tool(failure_error_function=safe_tool_error)
def search_repository_text(
    wrapper: RunContextWrapper[AnalysisRunContext],
    query: str,
    relative_path: str = "",
) -> str:
    """Search allowed repository text with conservative result and excerpt limits."""
    result = search_text(
        wrapper.context.repository, wrapper.context.config, query, relative_path
    )
    return result.model_dump_json()


REPOSITORY_TOOLS = [
    get_repository_context,
    list_repository_tree,
    read_repository_file,
    search_repository_text,
]
