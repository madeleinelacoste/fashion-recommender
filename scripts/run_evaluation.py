"""Build every recommender, score it on the held-out week and save the comparison tables."""
import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fashion_recs.db import connect, query  # noqa: E402
from fashion_recs.metrics import evaluate, per_customer_ap  # noqa: E402
from fashion_recs.recommenders import build_all  # noqa: E402

# Starting weights for the hybrid; tune them on a validation week, not the test week.
HYBRID_WEIGHTS = {"repurchase": 1.0, "co_purchase": 0.5, "popular_by_age_band": 0.2}


def main(db_path, out_dir: Path):
    con = connect(db_path)
    targets = query(con, "test_customers")
    actual = dict(zip(targets["customer_id"], targets["articles"].map(list)))
    models = build_all(con, list(actual), HYBRID_WEIGHTS)

    overall = pd.DataFrame({name: evaluate(actual, recs) for name, recs in models.items()}).T
    overall = overall.sort_values("map@12")

    segment_of = dict(zip(targets["customer_id"], targets["segment"]))
    by_segment = pd.DataFrame({
        name: pd.Series(per_customer_ap(actual, recs)).groupby(segment_of).mean()
        for name, recs in models.items()
    })
    by_segment.insert(0, "customers", pd.Series(segment_of).value_counts())

    out_dir.mkdir(parents=True, exist_ok=True)
    overall.to_csv(out_dir / "model_comparison.csv", index_label="model")
    by_segment.to_csv(out_dir / "map12_by_segment.csv", index_label="segment")

    pd.set_option("display.float_format", "{:.4f}".format)
    print(f"Evaluated {len(actual):,} customers who bought in the test week\n")
    print(overall.to_string(), "\n")
    print("MAP@12 by customer segment")
    print(by_segment.to_string())


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", default=None, help="defaults to $RECS_DB or data/hm.duckdb")
    p.add_argument("--out-dir", type=Path, default=ROOT / "results")
    a = p.parse_args()
    main(a.db, a.out_dir)
