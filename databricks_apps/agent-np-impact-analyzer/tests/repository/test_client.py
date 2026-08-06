from io import BytesIO
from types import SimpleNamespace

import pytest

from agent_server.repository.client import DatabricksRepositoryClient
from agent_server.repository.errors import RepositoryAccessError, RepositoryErrorCode


def test_get_context_accepts_exact_repo(fake_workspace_client, config):
    client = DatabricksRepositoryClient(fake_workspace_client, config)

    context = client.get_context()

    assert context.repo_id == config.repo_id
    assert context.path == config.root
    assert context.branch == config.branch
    assert context.head_commit_id == "9c48831022a329902f765058de37e6d0a1528eb7"
    fake_workspace_client.repos.get.assert_called_once_with(config.repo_id)


def test_get_context_rejects_branch_mismatch(fake_workspace_client, config):
    fake_workspace_client.repos.get.return_value.branch = "develop"

    with pytest.raises(RepositoryAccessError) as error:
        DatabricksRepositoryClient(fake_workspace_client, config).get_context()

    assert error.value.code == RepositoryErrorCode.BRANCH_NOT_ALLOWED


def test_get_context_rejects_other_repository_mismatch(fake_workspace_client, config):
    fake_workspace_client.repos.get.return_value.url = "https://github.com/other/repository.git"

    with pytest.raises(RepositoryAccessError) as error:
        DatabricksRepositoryClient(fake_workspace_client, config).get_context()

    assert error.value.code == RepositoryErrorCode.REPOSITORY_CONTEXT_MISMATCH


def test_list_tree_recurses_within_bounds_and_excludes_disallowed_files(
    fake_workspace_client, config
):
    root = config.root
    fake_workspace_client.workspace.list.side_effect = [
        iter(
            [
                SimpleNamespace(path=f"{root}/README.md", object_type="FILE", size=18),
                SimpleNamespace(path=f"{root}/.env", object_type="FILE", size=10),
                SimpleNamespace(path=f"{root}/notebooks", object_type="DIRECTORY", size=None),
            ]
        ),
        iter(
            [
                SimpleNamespace(
                    path=f"{root}/notebooks/silver.py", object_type="FILE", size=20
                )
            ]
        ),
    ]
    client = DatabricksRepositoryClient(fake_workspace_client, config)

    entries = client.list_tree()

    assert [(entry.relative_path, entry.object_type) for entry in entries] == [
        ("README.md", "FILE"),
        ("notebooks/silver.py", "FILE"),
    ]
    assert fake_workspace_client.workspace.list.call_count == 2


def test_read_file_uses_only_workspace_download(fake_workspace_client, config):
    client = DatabricksRepositoryClient(fake_workspace_client, config)

    result = client.read_file("README.md")

    assert result.relative_path == "README.md"
    assert result.content.startswith("# Naturapet_DLH")
    assert result.size_bytes == 18
    fake_workspace_client.workspace.download.assert_called_once()


def test_read_file_rejects_content_larger_than_configured_limit(fake_workspace_client, config):
    fake_workspace_client.workspace.get_status.return_value = SimpleNamespace(
        size=config.max_file_bytes + 1, object_type="FILE"
    )

    with pytest.raises(RepositoryAccessError) as error:
        DatabricksRepositoryClient(fake_workspace_client, config).read_file("README.md")

    assert error.value.code == RepositoryErrorCode.FILE_TOO_LARGE
    fake_workspace_client.workspace.download.assert_not_called()


def test_read_file_redacts_sensitive_content(fake_workspace_client, config):
    fake_workspace_client.workspace.download.return_value = BytesIO(
        b'client_secret = "do-not-return-me"\nmode = "dev"\n'
    )
    fake_workspace_client.workspace.get_status.return_value = SimpleNamespace(
        size=47, object_type="FILE"
    )

    result = DatabricksRepositoryClient(fake_workspace_client, config).read_file("settings.py")

    assert result.redacted is True
    assert "do-not-return-me" not in result.content
    assert "[REDACTED]" in result.content


def test_read_file_maps_sdk_failures_to_safe_read_error(fake_workspace_client, config):
    fake_workspace_client.workspace.get_status.side_effect = RuntimeError("token=secret")

    with pytest.raises(RepositoryAccessError) as error:
        DatabricksRepositoryClient(fake_workspace_client, config).read_file("README.md")

    assert error.value.code == RepositoryErrorCode.DATABRICKS_READ_ERROR
    assert "secret" not in error.value.safe_message


@pytest.mark.parametrize("method_name", ["write", "upload", "import", "delete", "run", "update"])
def test_client_exposes_no_mutating_method(fake_workspace_client, config, method_name):
    client = DatabricksRepositoryClient(fake_workspace_client, config)

    assert not hasattr(client, method_name)
