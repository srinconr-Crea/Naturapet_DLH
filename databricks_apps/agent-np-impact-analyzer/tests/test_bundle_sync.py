"""Bundle packaging boundaries for local development artifacts."""

from pathlib import Path

from ruamel.yaml import YAML


def test_bundle_sync_excludes_local_python_test_caches():
    """Pytest and bytecode caches cannot make bundle validation depend on local state."""
    bundle_path = Path(__file__).parents[1] / "databricks.yml"
    bundle = YAML(typ="safe").load(bundle_path.read_text(encoding="utf-8"))

    assert {
        ".pytest_cache/**",
        "**/.pytest_cache/**",
        "**/__pycache__/**",
        "**/*.pyc",
    }.issubset(set(bundle["sync"]["exclude"]))
