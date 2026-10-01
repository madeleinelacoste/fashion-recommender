"""Load the raw CSVs into DuckDB and build the train/test tables (sql/00_build_tables.sql)."""
import argparse
import time
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]


def main(raw_dir: Path, db_path: Path, customer_pct: int):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.unlink(missing_ok=True)
    con = duckdb.connect(str(db_path))
    # Read IDs as text so article IDs keep their leading zero.
    cust_id = "types={'customer_id': 'VARCHAR'}"
    art_id = "types={'article_id': 'VARCHAR'}"
    both_ids = "types={'customer_id': 'VARCHAR', 'article_id': 'VARCHAR'}"
    sample = f"WHERE hash(customer_id) % 100 < {customer_pct}" if customer_pct < 100 else ""

    started = time.time()
    con.execute(f"""
        CREATE TABLE customers AS
        SELECT * FROM read_csv('{raw_dir / "customers.csv"}', header=true, {cust_id}) {sample};
        CREATE TABLE articles AS
        SELECT * FROM read_csv('{raw_dir / "articles.csv"}', header=true, {art_id});
        CREATE TABLE transactions AS
        SELECT CAST(t_dat AS DATE) AS t_dat, customer_id, article_id, price, sales_channel_id
        FROM read_csv('{raw_dir / "transactions_train.csv"}', header=true, {both_ids}) {sample};
    """)
    con.execute((ROOT / "sql" / "00_build_tables.sql").read_text())

    for table in ["transactions", "train", "test_purchases", "customer_segments", "articles"]:
        n = con.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
        print(f"{table:<20}{n:>12,}")
    test_start, test_end = con.execute("SELECT * FROM split").fetchone()
    print(f"Test week: {test_start} to {test_end}  ({time.time() - started:.0f}s)")
    con.close()


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--raw-dir", type=Path, default=ROOT / "data" / "raw")
    p.add_argument("--db", type=Path, default=ROOT / "data" / "hm.duckdb")
    p.add_argument("--customer-pct", type=int, default=100,
                   help="keep a random %% of customers (e.g. 20 on a low-memory laptop)")
    a = p.parse_args()
    main(a.raw_dir, a.db, a.customer_pct)
