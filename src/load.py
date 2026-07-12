import sqlite3
from pathlib import Path

from src.transform import pipeline_transform

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "processed" / "warehouse.db"
TABLE_NAME = "fat_custo_manutencao"


def carregar_no_warehouse(df, db_path=DB_PATH):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        df.to_sql(TABLE_NAME, conn, if_exists="replace", index=False)


def pipeline_completo():
    df = pipeline_transform()
    carregar_no_warehouse(df)
    print(f"{len(df)} linhas carregadas em {DB_PATH}")


if __name__ == "__main__":
    pipeline_completo()
