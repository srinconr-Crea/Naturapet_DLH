import json
import uuid
from datetime import datetime
from typing import Dict

from src.common.config import (
    build_audit_table_fqn,
    build_bronze_table_path,
    build_historic_file_path,
    get_config,
)
from src.common.delta_load import (
    add_ingestion_metadata,
    append_audit_records,
    build_audit_record,
    create_or_merge_delta,
    ensure_catalog_schema,
    list_pending_archives,
    update_archive_status,
)
from src.common.io import (
    discover_area_files,
    dumps_task_value,
    move_file_to_historic,
    path_exists,
    read_source_file,
)
from src.common.schema import (
    build_primary_key_map,
    conform_to_dictionary,
    load_data_dictionary,
    normalize_table_name,
    validate_expected_columns,
    with_hash_key_if_needed,
)
from src.common.validation import (
    validate_mes_carga_alignment,
    validate_non_empty_dataframe,
    validate_table_known_or_allowed,
)


def run_bronze_load(spark, dbutils, area: str) -> Dict[str, object]:
    config = get_config(spark=spark, area=area)
    ensure_catalog_schema(spark, config["catalog"], config["bronze_schema"])

    dictionary_map = load_data_dictionary(spark, config["data_dictionary_path"])
    primary_key_map = build_primary_key_map(dictionary_map)
    audit_table = build_audit_table_fqn(config)
    source_files = discover_area_files(dbutils, config["raw_year_path"])

    processed_files = []
    failed_files = []

    for source_file in source_files:
        table_name = normalize_table_name(
            source_file["source_file_name"],
            source_file["source_month"] or "",
        )
        target_table = (
            f"`{config['catalog']}`.`{config['bronze_schema']}`.`{table_name}`"
        )
        target_path = build_bronze_table_path(config, table_name)
        historic_path = build_historic_file_path(
            config,
            source_file["source_file_name"],
            source_file["source_month"],
        )
        load_id = str(uuid.uuid4())

        try:
            validate_table_known_or_allowed(table_name, dictionary_map)
            dataframe = read_source_file(
                spark=spark,
                path=source_file["source_path"],
                source_format=source_file["source_format"],
                schema=None,
                header=True,
            )
            validate_non_empty_dataframe(dataframe, table_name)
            validate_expected_columns(dataframe, table_name, dictionary_map)
            dataframe = conform_to_dictionary(dataframe, table_name, dictionary_map)
            validate_mes_carga_alignment(
                dataframe,
                table_name,
                config["data_year"],
                source_file["source_month"],
            )
            dataframe = add_ingestion_metadata(
                dataframe,
                area=config["area"],
                source_year=config["data_year"],
                source_month=source_file["source_month"],
                source_path=source_file["source_path"],
                source_file_name=source_file["source_file_name"],
                load_mode=source_file["load_mode"],
            )
            dataframe, merge_keys = with_hash_key_if_needed(
                dataframe,
                table_name,
                primary_key_map,
            )
            create_or_merge_delta(
                spark=spark,
                dataframe=dataframe,
                target_table=target_table,
                target_path=target_path,
                merge_keys=merge_keys,
            )

            record_count = dataframe.count()
            append_audit_records(
                spark=spark,
                audit_records=[
                    build_audit_record(
                        load_id=load_id,
                        area=config["area"],
                        table_name=table_name,
                        load_mode=source_file["load_mode"],
                        source_year=config["data_year"],
                        source_month=source_file["source_month"],
                        source_path=source_file["source_path"],
                        source_file_name=source_file["source_file_name"],
                        source_format=source_file["source_format"],
                        target_table=target_table,
                        target_path=target_path,
                        record_count=record_count,
                        status="SUCCESS",
                        error_message=None,
                        historic_path=historic_path,
                    )
                ],
                audit_table=audit_table,
                audit_table_path=config["audit_table_path"],
            )

            processed_files.append(
                {
                    "table_name": table_name,
                    "source_file_name": source_file["source_file_name"],
                    "source_month": source_file["source_month"],
                    "load_mode": source_file["load_mode"],
                    "source_format": source_file["source_format"],
                    "record_count": record_count,
                    "target_table": target_table,
                    "target_path": target_path,
                }
            )
        except Exception as error:
            append_audit_records(
                spark=spark,
                audit_records=[
                    build_audit_record(
                        load_id=load_id,
                        area=config["area"],
                        table_name=table_name,
                        load_mode=source_file["load_mode"],
                        source_year=config["data_year"],
                        source_month=source_file["source_month"],
                        source_path=source_file["source_path"],
                        source_file_name=source_file["source_file_name"],
                        source_format=source_file["source_format"],
                        target_table=target_table,
                        target_path=target_path,
                        record_count=None,
                        status="FAILED",
                        error_message=str(error),
                        historic_path=historic_path,
                    )
                ],
                audit_table=audit_table,
                audit_table_path=config["audit_table_path"],
            )
            failed_files.append(
                {
                    "table_name": table_name,
                    "source_file_name": source_file["source_file_name"],
                    "error": str(error),
                }
            )

    summary = {
        "status": "ERROR" if failed_files else "OK",
        "area": config["area"],
        "environment": config["env"],
        "catalog": config["catalog"],
        "bronze_schema": config["bronze_schema"],
        "processed_files": processed_files,
        "failed_files": failed_files,
    }

    dbutils.jobs.taskValues.set(
        key=f"{config['area']}_bronze_load_summary",
        value=dumps_task_value(summary),
    )

    if failed_files:
        raise RuntimeError(json.dumps(summary, ensure_ascii=False))

    return summary


def run_bronze_archive(spark, dbutils, area: str) -> Dict[str, object]:
    config = get_config(spark=spark, area=area)
    audit_table = build_audit_table_fqn(config)

    archived_files = []
    archive_failures = []
    updates = []

    for row in list_pending_archives(spark, audit_table):
        now = datetime.utcnow()
        try:
            if path_exists(dbutils, row["source_path"]):
                move_file_to_historic(
                    dbutils=dbutils,
                    source_path=row["source_path"],
                    target_path=row["historic_path"],
                )
            elif not path_exists(dbutils, row["historic_path"]):
                raise FileNotFoundError(
                    f"No existe ni el origen {row['source_path']} ni el historico "
                    f"{row['historic_path']}."
                )

            updates.append(
                {
                    "load_id": row["load_id"],
                    "archived_at": now,
                    "archive_status": "SUCCESS",
                    "archive_error_message": None,
                    "updated_at": now,
                }
            )
            archived_files.append(
                {
                    "table_name": row["table_name"],
                    "source_file_name": row["source_file_name"],
                    "historic_path": row["historic_path"],
                }
            )
        except Exception as error:
            updates.append(
                {
                    "load_id": row["load_id"],
                    "archived_at": None,
                    "archive_status": "FAILED",
                    "archive_error_message": str(error),
                    "updated_at": now,
                }
            )
            archive_failures.append(
                {
                    "table_name": row["table_name"],
                    "source_file_name": row["source_file_name"],
                    "error": str(error),
                }
            )

    update_archive_status(spark, audit_table, updates)

    summary = {
        "status": "ERROR" if archive_failures else "OK",
        "area": config["area"],
        "environment": config["env"],
        "archived_files": archived_files,
        "archive_failures": archive_failures,
    }

    dbutils.jobs.taskValues.set(
        key=f"{config['area']}_bronze_archive_summary",
        value=dumps_task_value(summary),
    )

    if archive_failures:
        raise RuntimeError(json.dumps(summary, ensure_ascii=False))

    return summary
