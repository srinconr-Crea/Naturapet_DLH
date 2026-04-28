# Databricks notebook source
# MAGIC %run ./_common

domain = globals().get("DOMAIN")
environment = ensure_text_widget("environment", "dev")
catalog_name = ensure_text_widget("catalog_name", f"naturapet_{environment}")
storage_account = ensure_text_widget("storage_account", "demodldb")
storage_container = ensure_text_widget("storage_container", "democodex")
data_year = ensure_text_widget("data_year", "2026")

if not domain:
    domain = ensure_text_widget("domain", "shared")

schema_name = f"{domain}_bronze"
external_domain_root = (
    f"abfss://{storage_container}@{storage_account}.dfs.core.windows.net/external/{environment}/{domain}/bronze"
)
audit_table = fully_qualified_name(catalog_name, schema_name, AUDIT_TABLE_NAME)

archive_updates = []
archive_failures = []
archived_files = []

for pending_record in pending_archive_records(audit_table):
    source_path = pending_record["source_path"]
    historic_path = pending_record["historic_path"]
    now = datetime.utcnow()

    try:
        if path_exists(source_path):
            dbutils.fs.mkdirs(parent_directory(historic_path))
            dbutils.fs.mv(source_path, historic_path)
        elif not path_exists(historic_path):
            raise FileNotFoundError(
                f"No existe la ruta origen {source_path} ni el historico esperado {historic_path}."
            )

        archive_updates.append(
            {
                "load_id": pending_record["load_id"],
                "archived_at": now,
                "archive_status": "SUCCESS",
                "archive_error_message": None,
                "updated_at": now,
            }
        )
        archived_files.append(
            {
                "table_name": pending_record["table_name"],
                "source_file_name": pending_record["source_file_name"],
                "historic_path": historic_path,
            }
        )
    except Exception as error:
        archive_updates.append(
            {
                "load_id": pending_record["load_id"],
                "archived_at": None,
                "archive_status": "FAILED",
                "archive_error_message": str(error),
                "updated_at": now,
            }
        )
        archive_failures.append(
            {
                "table_name": pending_record["table_name"],
                "source_file_name": pending_record["source_file_name"],
                "error": str(error),
            }
        )

update_archive_status(audit_table, archive_updates)

summarize_results(
    {
        "domain": domain,
        "environment": environment,
        "archived_files": len(archived_files),
        "archive_failures": len(archive_failures),
        "files": archived_files,
        "errors": archive_failures,
    }
)

if archive_failures:
    raise RuntimeError(f"Fallaron {len(archive_failures)} archivo(s) al mover a historic para {domain}.")
