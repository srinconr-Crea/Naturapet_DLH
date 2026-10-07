"""Local behavior checks for the final Gold quality notebook steps."""

import ast
import json
import unittest
from pathlib import Path
from types import SimpleNamespace


NOTEBOOK = Path(__file__).resolve().parents[1] / "notebooks/gobierno/gold/05_quality_checks.ipynb"


def run_quality_tail(rows):
    source = "\n".join(
        "".join(cell["source"])
        for cell in json.loads(NOTEBOOK.read_text(encoding="utf-8"))["cells"]
        if cell["cell_type"] == "code"
    )
    tree = ast.parse(source)
    write_gold = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "write_gold")
    tail_start = next(
        index
        for index, node in enumerate(tree.body)
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "summary" for target in node.targets)
    )
    program = ast.Module(body=[write_gold, *tree.body[tail_start:]], type_ignores=[])
    events = []
    tables = {}

    class Frame:
        def __init__(self, values):
            self.values = values
            self.write = self

        def withColumn(self, *_args):
            return self

        def format(self, *_args):
            return self

        def mode(self, *_args):
            return self

        def option(self, *_args):
            return self

        def saveAsTable(self, table):
            events.append(("save", table))
            tables[table] = self

        def count(self):
            return len(self.values)

        def select(self, *_columns):
            return self

        def collect(self):
            events.append(("collect",))
            return [SimpleNamespace(**value) for value in self.values]

    checks = Frame(rows)
    spark = SimpleNamespace(
        table=lambda name: tables[name],
        createDataFrame=lambda summary: summary,
    )
    namespace = {
        "F": SimpleNamespace(lit=lambda value: value, current_timestamp=lambda: None),
        "checks": checks,
        "spark": spark,
        "gold_schema": "gobierno_gold",
        "gold_root": "abfss://test/gold",
        "full_name": lambda schema, name: f"`{schema}`.`{name}`",
        "display": lambda _summary: events.append(("display",)),
    }
    try:
        exec(compile(program, str(NOTEBOOK), "exec"), namespace)
    except ValueError as error:
        return events, str(error)
    return events, None


class GoldQualityGateTests(unittest.TestCase):
    def test_pass_month_succeeds_after_publication(self):
        events, error = run_quality_tail([{"mes_carga": "2026-01", "gold_quality_status": "PASS"}])
        self.assertIsNone(error)
        self.assertIn(("save", "`gobierno_gold`.`gold_quality_checks`"), events)

    def test_fail_month_is_named_in_error(self):
        events, error = run_quality_tail([{"mes_carga": "2026-01", "gold_quality_status": "FAIL"}])
        self.assertIsNotNone(error)
        self.assertIn("2026-01", error)
        self.assertIn(("save", "`gobierno_gold`.`gold_quality_checks`"), events)

    def test_null_status_is_named_in_error(self):
        _, error = run_quality_tail([{"mes_carga": "2026-02", "gold_quality_status": None}])
        self.assertIsNotNone(error)
        self.assertIn("2026-02", error)

    def test_empty_result_keeps_existing_staging_failure(self):
        events, error = run_quality_tail([])
        self.assertIn("no contiene registros para publicar", error)
        self.assertNotIn(("save", "`gobierno_gold`.`gold_quality_checks`"), events)

    def test_publication_precedes_quality_failure_for_multiple_months(self):
        events, error = run_quality_tail(
            [
                {"mes_carga": "2026-01", "gold_quality_status": "PASS"},
                {"mes_carga": "2026-02", "gold_quality_status": "FAIL"},
                {"mes_carga": "2026-03", "gold_quality_status": None},
            ]
        )
        self.assertIsNotNone(error)
        self.assertIn("2026-02", error)
        self.assertIn("2026-03", error)
        self.assertLess(
            events.index(("save", "`gobierno_gold`.`gold_quality_checks`")),
            events.index(("collect",)),
        )


if __name__ == "__main__":
    unittest.main()
