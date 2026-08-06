from agent_server.config import RepositoryConfig


def test_repository_config_has_fixed_limits():
    config = RepositoryConfig()

    assert config.repo_id == 1393361128272538
    assert config.root == "/Workspace/Naturapet_BI/practica-margen-silver"
    assert config.branch == "practica-margen-silver"
    assert config.max_files == 200
    assert config.max_file_bytes == 1_048_576
    assert config.max_results == 30
