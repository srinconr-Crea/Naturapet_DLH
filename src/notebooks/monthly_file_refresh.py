import argparse
from pyspark.sql import functions as F


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--schema", required=True)
    parser.add_argument("--external-base-path", required=True)
    parser.add_argument("--table-name", required=True)
    return parser.parse_args()


def main():
    args = parse_args()

    target_table = f"{args.catalog}.{args.schema}.{args.table_name}"
    target_path = f"{args.external_base_path}/{args.schema}/{args.table_name}"

    # Placeholder inicial: reemplazar por la logica real de lectura mensual de Naturapet.
    df = spark.createDataFrame(
        [
            ("monthly-run", "pending-naturapet-source-definition"),
        ],
        ["process_name", "status"],
    ).withColumn("load_timestamp", F.current_timestamp())

    (
        df.write.format("delta")
        .mode("overwrite")
        .option("path", target_path)
        .saveAsTable(target_table)
    )

    print(f"Tabla actualizada: {target_table}")
    print(f"Ruta externa: {target_path}")


if __name__ == "__main__":
    main()
