"""Immutable configuration for guarded repository access."""

import os

from pydantic import BaseModel, ConfigDict


class RepositoryConfig(BaseModel):
    """Repository constraints that remain fixed after configuration is loaded."""

    model_config = ConfigDict(frozen=True)

    repo_id: int = 1393361128272538
    root: str = "/Workspace/Naturapet_BI/practica-margen-silver"
    url: str = "https://github.com/srinconr-Crea/Naturapet_DLH.git"
    provider: str = "gitHub"
    branch: str = "practica-margen-silver"
    allowed_extensions: frozenset[str] = frozenset(
        {".py", ".ipynb", ".sql", ".yml", ".yaml", ".json", ".toml", ".md", ".txt"}
    )
    max_files: int = 200
    max_file_bytes: int = 1_048_576
    max_results: int = 30
    max_results_per_file: int = 5
    max_depth: int = 12
    max_excerpt_chars: int = 500

    @classmethod
    def from_environment(cls) -> "RepositoryConfig":
        """Create configuration from the Task 1 repository environment variables."""
        return cls(
            repo_id=int(os.getenv("NP_REPOSITORY_ID", "1393361128272538")),
            root=os.getenv("NP_REPOSITORY_ROOT", cls.model_fields["root"].default),
            url=os.getenv("NP_REPOSITORY_URL", cls.model_fields["url"].default),
            provider=os.getenv("NP_REPOSITORY_PROVIDER", cls.model_fields["provider"].default),
            branch=os.getenv("NP_REPOSITORY_BRANCH", cls.model_fields["branch"].default),
        )
