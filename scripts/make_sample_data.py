"""Generate a small SYNTHETIC dataset with the same columns as the Kaggle CSVs.

Use it to test the pipeline without the 3GB download. Customers get a couple of
favourite garment groups and sometimes rebuy items, so the recommenders have some
signal to find, but the results mean nothing about real shopping behaviour.
"""
import argparse
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

GARMENT_GROUPS = ["Jersey Basic", "Jersey Fancy", "Trousers", "Dresses Ladies", "Knitwear",
                  "Blouses", "Shoes", "Accessories", "Under-, Nightwear", "Outdoor",
                  "Swimwear", "Socks and Tights"]
PRODUCT_TYPES = ["T-shirt", "Top", "Trousers", "Dress", "Sweater", "Blouse", "Sneakers",
                 "Bag", "Bra", "Jacket", "Bikini top", "Socks"]
COLOURS = ["Black", "White", "Dark Blue", "Beige", "Grey", "Light Pink", "Red", "Green"]


def main(out_dir: Path, n_customers: int, n_articles: int, weeks: int, seed: int):
    rng = np.random.default_rng(seed)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Articles: each belongs to a garment group and has a launch week and a base popularity.
    group_idx = rng.integers(0, len(GARMENT_GROUPS), n_articles)
    articles = pd.DataFrame({
        "article_id": [f"0{100000000 + i}" for i in range(n_articles)],
        "product_type_name": [PRODUCT_TYPES[g] for g in group_idx],
        "product_group_name": ["Garment"] * n_articles,
        "colour_group_name": rng.choice(COLOURS, n_articles),
        "garment_group_name": [GARMENT_GROUPS[g] for g in group_idx],
        "index_group_name": rng.choice(["Ladieswear", "Menswear", "Divided", "Sport"], n_articles),
        "detail_desc": "Synthetic article",
    })
    launch_week = rng.integers(-8, weeks, n_articles)
    base_pop = rng.pareto(1.2, n_articles) + 0.1

    customers = pd.DataFrame({
        "customer_id": [f"{i:064x}" for i in rng.integers(0, 2**62, n_customers)],
        "club_member_status": rng.choice(["ACTIVE", "PRE-CREATE"], n_customers, p=[0.9, 0.1]),
        "fashion_news_frequency": rng.choice(["NONE", "Regularly"], n_customers),
        "age": np.where(rng.random(n_customers) < 0.02, np.nan,
                        rng.integers(16, 75, n_customers)),
    })

    start = date(2020, 9, 22) - timedelta(weeks=weeks)
    rows = []
    for cust in customers["customer_id"]:
        favourites = rng.choice(len(GARMENT_GROUPS), 2, replace=False)
        visits = rng.poisson(rng.uniform(0.2, 1.5) * weeks / 4)
        bought = []
        for day in np.sort(rng.integers(0, weeks * 7, visits)):
            week = day // 7
            # Articles on sale: launched, not too old; recent launches sell best.
            age = week - launch_week
            live = np.flatnonzero((age >= 0) & (age < 12))
            if live.size == 0:
                continue
            weight = base_pop[live] * np.exp(-age[live] / 4)
            weight[np.isin(group_idx[live], favourites)] *= 6
            for _ in range(rng.integers(1, 5)):
                if bought and rng.random() < 0.15:
                    art = bought[rng.integers(len(bought))]  # rebuy (another size / colour)
                else:
                    art = rng.choice(live, p=weight / weight.sum())
                bought.append(art)
                rows.append((start + timedelta(days=int(day)), cust, art,
                             round(rng.uniform(0.005, 0.08), 6), int(rng.choice([1, 2]))))

    tx = pd.DataFrame(rows, columns=["t_dat", "customer_id", "article_idx", "price",
                                     "sales_channel_id"])
    tx["article_id"] = articles["article_id"].to_numpy()[tx.pop("article_idx")]
    tx = tx[["t_dat", "customer_id", "article_id", "price", "sales_channel_id"]].sort_values("t_dat")

    tx.to_csv(out_dir / "transactions_train.csv", index=False)
    articles.to_csv(out_dir / "articles.csv", index=False)
    customers.to_csv(out_dir / "customers.csv", index=False)
    print(f"Wrote {len(tx):,} transactions, {n_articles:,} articles, "
          f"{n_customers:,} customers to {out_dir}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out-dir", type=Path, default=ROOT / "data" / "sample")
    p.add_argument("--customers", type=int, default=5000)
    p.add_argument("--articles", type=int, default=2000)
    p.add_argument("--weeks", type=int, default=26)
    p.add_argument("--seed", type=int, default=42)
    a = p.parse_args()
    main(a.out_dir, a.customers, a.articles, a.weeks, a.seed)
