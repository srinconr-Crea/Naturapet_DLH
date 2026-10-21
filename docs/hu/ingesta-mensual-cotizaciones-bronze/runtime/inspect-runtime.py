# Databricks notebook source
"""Inspect only this approved synthetic run; never access NaturaPet catalogs."""
import json

CATALOG = "crea_cotizaciones_test_20261020_01a15a7c"
try:
    test_run_id = dbutils.widgets.get("test_run_id")
except Exception:
    test_run_id = "runtime_attempt01"
assert test_run_id in ("runtime_attempt01", "runtime_attempt02", "runtime_attempt03"), "Unapproved inspection run"
ROOT = "abfss://demo@demodldb.dfs.core.windows.net/_tests/cotizaciones/20261020_01a15a7c/data/" + test_run_id
assert not CATALOG.lower().startswith("naturapet")
assert ROOT.startswith("abfss://demo@demodldb.dfs.core.windows.net/_tests/cotizaciones/20261020_01a15a7c/data/")
events = json.loads(dbutils.fs.head(ROOT + "/_inventory.json", 10 * 1024 * 1024))
assert isinstance(events, list) and events, "Inventory missing"
runtime = next(event["metadata"] for event in events if event.get("kind") == "runtime")
assert runtime["catalog"] == CATALOG
assert runtime["compute"] == "1020-210854-9y22c5h7"
assert runtime["storage_root"] == ROOT
tables = [row.asDict() for row in spark.sql(
    "SELECT table_catalog, table_schema, table_name, table_type "
    "FROM " + CATALOG + ".information_schema.tables "
    "WHERE table_schema <> 'information_schema' ORDER BY table_schema, table_name"
).collect()]
schemas = [row[0] for row in spark.sql("SHOW SCHEMAS IN " + CATALOG).collect()]
assert all(table["table_catalog"] == CATALOG for table in tables)
resources = sorted({(event.get("kind", ""), event.get("name", ""), event.get("state", ""))
                    for event in events if event.get("kind") in ("delta_path", "table", "schema")})
result = {
    "runtime": runtime,
    "schema_names": schemas,
    "tables": tables,
    "inventory_event_count": len(events),
    "recorded_resources": [{"kind": kind, "name": name, "state": state}
                           for kind, name, state in resources],
    "retention": "Synthetic catalog, data, workspace sources and run history retained; temporary cluster will be terminated.",
}
# Visible copy permits subsequent SQL warehouse inspection (underscore files are hidden).
dbutils.fs.put(ROOT + "/inventory.json", json.dumps(events, ensure_ascii=False), True)
dbutils.fs.put(ROOT + "/resource-summary.json", json.dumps(result, ensure_ascii=False), True)
dbutils.notebook.exit(json.dumps(result, ensure_ascii=False))
