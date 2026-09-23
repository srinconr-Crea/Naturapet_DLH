"""Regression checks for the published Gold quality gate."""

import ast
import json
from pathlib import Path


NOTEBOOK = Path(__file__).resolve().parents[1] / "notebooks/gobierno/gold/05_quality_checks.ipynb"


def notebook_source():
    return "".join(json.loads(NOTEBOOK.read_text(encoding="utf-8"))["cells"][0]["source"])


def gate_function():
    tree = ast.parse(notebook_source())
    node = next(item for item in tree.body if isinstance(item, ast.FunctionDef) and item.name == "assert_quality_passed")
    scope = {}
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(NOTEBOOK), "exec"), scope)
    return scope["assert_quality_passed"]


def test_all_months_pass():
    gate_function()([{"mes_carga": "2026-01", "gold_quality_status": "PASS"}])


def test_failed_month_is_reported():
    import pytest

    with pytest.raises(ValueError, match="2026-02"):
        gate_function()([{"mes_carga": "2026-02", "gold_quality_status": "FAIL"}])


def test_null_status_is_reported():
    import pytest

    with pytest.raises(ValueError, match="2026-03"):
        gate_function()([{"mes_carga": "2026-03", "gold_quality_status": None}])


def test_gate_runs_after_publication():
    source = notebook_source()
    assert source.index('write_gold(checks, "gold_quality_checks")') < source.rindex("assert_quality_passed(")
    assert source.rindex("assert_quality_passed(") < source.index("display(spark.createDataFrame(summary))")


def test_empty_result_keeps_existing_publication_error():
    import pytest

    node = next(item for item in ast.parse(notebook_source()).body if isinstance(item, ast.FunctionDef) and item.name == "write_gold")

    class Chain:
        def __getattr__(self, name):
            return self if name == "write" else lambda *args, **kwargs: self

        def count(self):
            return 0

    class Spark:
        def table(self, name):
            return Chain()

    class Functions:
        def lit(self, value):
            return value

        def current_timestamp(self):
            return None

    scope = {"F": Functions(), "spark": Spark(), "gold_root": "test", "gold_schema": "test", "full_name": lambda schema, name: f"{schema}.{name}"}
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(NOTEBOOK), "exec"), scope)
    with pytest.raises(ValueError, match="no contiene registros"):
        scope["write_gold"](Chain(), "gold_quality_checks")
