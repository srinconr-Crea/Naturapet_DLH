from pathlib import Path

from ruamel.yaml import YAML

from agent_server.config import RepositoryConfig, model_endpoint_from_environment


def test_repository_config_has_fixed_limits():
    config = RepositoryConfig()

    assert config.repo_id == 1393361128272538
    assert config.root == "/Workspace/Naturapet_BI/practica-margen-silver"
    assert config.branch == "practica-margen-silver"
    assert config.max_files == 200
    assert config.max_file_bytes == 1_048_576
    assert config.max_results == 30


def test_model_endpoint_is_loaded_from_environment(monkeypatch):
    monkeypatch.setenv("NP_MODEL_ENDPOINT", "databricks-gpt-5-mini")

    assert model_endpoint_from_environment() == "databricks-gpt-5-mini"


def test_bundle_omits_user_api_scopes_for_app_only_non_obo_identity():
    bundle_path = Path(__file__).parents[1] / "databricks.yml"
    bundle = YAML(typ="safe").load(bundle_path)

    app = bundle["resources"]["apps"]["np_impact_analyzer"]

    assert "user_api_scopes" not in app


def test_bundle_grants_app_query_access_to_the_live_llm_endpoint():
    bundle_path = Path(__file__).parents[1] / "databricks.yml"
    bundle = YAML(typ="safe").load(bundle_path)
    resources = bundle["resources"]["apps"]["np_impact_analyzer"]["resources"]

    llm_resource = next(resource for resource in resources if resource["name"] == "llm")

    assert llm_resource == {
        "name": "llm",
        "serving_endpoint": {
            "name": "databricks-claude-sonnet-4-6",
            "permission": "CAN_QUERY",
        },
    }

    env = bundle["resources"]["apps"]["np_impact_analyzer"]["config"]["env"]
    model_env = next(item for item in env if item["name"] == "NP_MODEL_ENDPOINT")
    assert model_env == {
        "name": "NP_MODEL_ENDPOINT",
        "value": "databricks-claude-sonnet-4-6",
    }


def test_app_yaml_exposes_the_same_model_endpoint():
    app_path = Path(__file__).parents[1] / "app.yaml"
    app = YAML(typ="safe").load(app_path)

    model_env = next(item for item in app["env"] if item["name"] == "NP_MODEL_ENDPOINT")
    assert model_env == {
        "name": "NP_MODEL_ENDPOINT",
        "value": "databricks-claude-sonnet-4-6",
    }
