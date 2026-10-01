"""Connect to the DuckDB database and run named queries from the sql/ folder.

Queries are marked with `-- name: query_name`, so the SQL files stay the single
source of truth and can also be run directly in the DuckDB CLI.
"""
import os
import re
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SQL_DIR = ROOT / "sql"
DEFAULT_DB = ROOT / "data" / "hm.duckdb"


def connect(db_path=None, read_only=True):
    path = db_path or os.environ.get("RECS_DB", DEFAULT_DB)
    return duckdb.connect(str(path), read_only=read_only)


def load_queries():
    """Return {name: sql} for every named query in sql/*.sql."""
    queries = {}
    for path in sorted(SQL_DIR.glob("*.sql")):
        blocks = re.split(r"^-- name:\s*(\w+)\s*$", path.read_text(), flags=re.M)
        for name, sql in zip(blocks[1::2], blocks[2::2]):
            queries[name] = sql.strip()
    return queries


def query(con, name, **params) -> pd.DataFrame:
    return con.execute(load_queries()[name], params or None).df()
