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
raw_environment_root = (
    f"abfss://{storage_container}@{storage_account}.dfs.core.windows.net/raw/{environment}"
)
raw_domain_root = f"{raw_environment_root}/{domain}"
external_domain_root = (
    f"abfss://{storage_container}@{storage_account}.dfs.core.windows.net/external/{environment}/{domain}/bronze"
)
historic_domain_root = (
    f"abfss://{storage_container}@{storage_account}.dfs.core.windows.net/historic/{domain}"
)

ensure_catalog_schema(catalog_name, schema_name)
primary_key_map = load_primary_key_map(raw_environment_root, data_year)
source_files = discover_source_files(raw_domain_root, data_year)
audit_table = fully_qualified_name(catalog_name, schema_name, AUDIT_TABLE_NAME)
audit_path = build_audit_table_path(external_domain_root, data_year)

processed_tables = []
failed_files = []

for source_file in source_files:
    load_id = str(uuid.uuid4())
    table_name = source_file["table_name"]
    source_month = source_file["source_month"]
    target_table = fully_qualified_name(catalog_name, schema_name, table_name)
    target_path = build_external_table_path(external_domain_root, data_year, table_name)
    historic_path = build_historic_file_path(
        historic_domain_root,
        data_year,
        source_file["source_file_name"],
        source_month,
    )

    try:
        source_dataframe = read_source_csv(source_file["source_path"])
        prepared_dataframe = add_ingestion_metadata(
            source_dataframe,
            domain,
            data_year,
            source_month,
            source_file["source_path"],
            source_file["source_file_name"],
            source_file["load_mode"],
        )
        prepared_dataframe, merge_keys = add_row_hash_if_needed(
            prepared_dataframe,
            primary_key_map.get(table_name, []),
        )
        merge_to_delta(prepared_dataframe, target_table, target_path, merge_keys)
        record_count = prepared_dataframe.count()

        append_audit_records(
            [
                audit_record(
                    load_id=load_id,
                    domain=domain,
                    table_name=table_name,
                    load_mode=source_file["load_mode"],
                    source_year=data_year,
                    source_month=source_month,
                    source_path=source_file["source_path"],
                    source_file_name=source_file["source_file_name"],
                    target_table=target_table,
                    target_path=target_path,
                    record_count=record_count,
                    status="SUCCESS",
                    error_message=None,
                    historic_path=historic_path,
                )
            ],
            audit_table,
            audit_path,
        )
        processed_tables.append(
            {
                "table_name": table_name,
                "source_file_name": source_file["source_file_name"],
                "record_count": record_count,
                "load_mode": source_file["load_mode"],
                "source_month": source_month,
            }
        )
    except Exception as error:
        append_audit_records(
            [
                audit_record(
                    load_id=load_id,
                    domain=domain,
                    table_name=table_name,
                    load_mode=source_file["load_mode"],
                    source_year=data_year,
                    source_month=source_month,
                    source_path=source_file["source_path"],
                    source_file_name=source_file["source_file_name"],
                    target_table=target_table,
                    target_path=target_path,
                    record_count=None,
                    status="FAILED",
                    error_message=str(error),
                    historic_path=historic_path,
                )
            ],
            audit_table,
            audit_path,
        )
        failed_files.append(
            {
                "table_name": table_name,
                "source_file_name": source_file["source_file_name"],
                "error": str(error),
            }
        )

summarize_results(
    {
        "domain": domain,
        "environment": environment,
        "catalog": catalog_name,
        "schema": schema_name,
        "processed_files": len(processed_tables),
        "failed_files": len(failed_files),
        "processed_tables": processed_tables,
        "errors": failed_files,
    }
)

if failed_files:
    raise RuntimeError(f"Fallaron {len(failed_files)} archivo(s) en la carga bronze de {domain}.")
