from pathlib import Path

from ruamel.yaml import YAML

from agent_server.config import RepositoryConfig


def test_repository_config_has_fixed_limits():
    config = RepositoryConfig()

    assert config.repo_id == 1393361128272538
    assert config.root == "/Workspace/Naturapet_BI/practica-margen-silver"
    assert config.branch == "practica-margen-silver"
    assert config.max_files == 200
    assert config.max_file_bytes == 1_048_576
    assert config.max_results == 30


def test_bundle_omits_user_api_scopes_for_app_only_non_obo_identity():
    bundle_path = Path(__file__).parents[1] / "databricks.yml"
    bundle = YAML(typ="safe").load(bundle_path)

    app = bundle["resources"]["apps"]["np_impact_analyzer"]

    assert "user_api_scopes" not in app
