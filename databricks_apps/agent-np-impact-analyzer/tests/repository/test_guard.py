import pytest

from agent_server.config import RepositoryConfig
from agent_server.repository.errors import RepositoryAccessError, RepositoryErrorCode
from agent_server.repository.guard import (
    normalize_relative_path,
    redact_sensitive_content,
    validate_file_policy,
)


@pytest.mark.parametrize(
    "candidate",
    [
        "../README.md",
        "notebooks/../../secret",
        "C:/temp/a.py",
        "/Workspace/Users/a.py",
    ],
)
def test_normalize_relative_path_blocks_escape(candidate):
    with pytest.raises(RepositoryAccessError) as error:
        normalize_relative_path(candidate)

    assert error.value.code == RepositoryErrorCode.PATH_NOT_ALLOWED


@pytest.mark.parametrize(
    "candidate",
    [".env", "secrets/client.pem", "config/id_rsa", ".git/config", "data/model.bin"],
)
def test_validate_file_policy_blocks_sensitive_or_binary_paths(candidate):
    with pytest.raises(RepositoryAccessError):
        validate_file_policy(candidate, size_bytes=100, config=RepositoryConfig())


def test_redact_sensitive_content_masks_assignment_values():
    content, redacted = redact_sensitive_content(
        'CLIENT_SECRET="sensitive-value"\nnormal_setting="visible"'
    )

    assert redacted is True
    assert "sensitive-value" not in content
    assert 'normal_setting="visible"' in content
