"""Profile-bound behavior for the optional discovery utility."""

import sys
from types import SimpleNamespace

import pytest

from scripts import discover_tools


def test_cli_discovery_commands_append_the_fixed_crea_dev_profile(monkeypatch):
    """A future CLI lookup cannot silently target the default workspace."""
    captured = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        return SimpleNamespace(stdout="{}")

    monkeypatch.setattr(discover_tools.subprocess, "run", fake_run)

    assert discover_tools.run_databricks_cli(["catalogs", "list"]) == "{}"
    assert captured["command"] == [
        "databricks",
        "catalogs",
        "list",
        "--profile",
        "CREA_DEV",
    ]


@pytest.mark.parametrize("profile_argument", ["OTHER_PROFILE", "DEFAULT"])
def test_discovery_rejects_user_selected_profiles(monkeypatch, profile_argument):
    """The parser must reject a profile switch instead of accepting another identity."""
    monkeypatch.setattr(
        sys,
        "argv",
        ["discover-tools", "--profile", profile_argument],
    )

    with pytest.raises(SystemExit) as error:
        discover_tools.main()

    assert error.value.code == 2


def test_discovery_uses_crea_dev_when_no_profile_argument_is_given(monkeypatch):
    """SDK discovery also uses CREA_DEV rather than the ambient default profile."""
    received = {}

    def workspace_client_factory(*, profile):
        received["profile"] = profile
        return object()

    monkeypatch.setattr(sys, "argv", ["discover-tools", "--format", "json"])
    monkeypatch.setattr(discover_tools, "WorkspaceClient", workspace_client_factory)
    for discovery_name in (
        "discover_uc_functions",
        "discover_uc_tables",
        "discover_vector_search_indexes",
        "discover_genie_spaces",
        "discover_custom_mcp_servers",
        "discover_external_mcp_servers",
    ):
        monkeypatch.setattr(discover_tools, discovery_name, lambda *_args, **_kwargs: [])

    discover_tools.main()

    assert received["profile"] == "CREA_DEV"
