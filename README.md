# Fashion Recommender

A personalized product recommendation system built on **31 million H&M transactions**,
comparing simple baselines with collaborative filtering and a hybrid model, and looking at
how well each one serves different types of customers.

This project follows on from
[Fashion Retail Intelligence](https://github.com/madeleinelacoste/fashion-retail-intelligence),
which used the same data to describe *what* sells and *who* buys. This one asks:
**given what a customer has bought so far, what will they buy next week?**

> 🚧 **Work in progress.** The baseline pipeline is built and tested on synthetic data.
> Results on the real dataset will be added below.

## Business Questions

1. **Baselines:** How far can simple rules (best sellers, "buy it again", "bought
   together") get before machine learning is needed?
2. **Personalization:** How much does collaborative filtering improve on those baselines,
   and for which customers?
3. **Customer segments:** Do recommendations work equally well for loyal, lapsed and new
   customers? Where should a CRM team trust the model, and where should it fall back to
   curated or trending picks?

## Tools & Technologies

- SQL (DuckDB)
- Python: pandas, NumPy, SciPy, Matplotlib
- Jupyter Notebook
- GitHub

## Dataset

[H&M Personalized Fashion Recommendations](https://www.kaggle.com/competitions/h-and-m-personalized-fashion-recommendations)
(Kaggle), September 2018 to September 2020: ~31.8M transactions, ~1.37M customers and
~105K articles. See [`data/README.md`](data/README.md) for download instructions.

## Evaluation Setup

The setup matches the original Kaggle competition:

- **Train:** all transactions before the final week.
- **Test:** the final 7 days (15 – 21 Sept 2020). Each model recommends **12 articles**
  per customer, and is scored only on customers who bought something that week.
- **Metric:** **MAP@12** (mean average precision at 12), which rewards placing purchased
  items near the top of the list. **Recall@12** is reported alongside it.

## Approach

| Model | Idea | Status |
|---|---|---|
| Popularity | Last week's 12 best sellers, same list for everyone | ✅ built |
| Popular by age band | Last week's best sellers within the customer's 10-year age band | ✅ built |
| Repurchase | Items the customer bought in the last 4 weeks, weighted by recency | ✅ built |
| Co-purchase | Items bought in the same basket as the customer's recent items | ✅ built |
| Hybrid | Weighted blend of the above, filled with best sellers | ✅ built |
| Collaborative filtering | Implicit-feedback matrix factorization (ALS) | ⬜ next |
| Content-based | Similar product type / colour / garment group | ⬜ planned |
| Learned ranker | Gradient-boosted model re-ranking the candidates | ⬜ stretch |

Every model's list is filled up to 12 with global best sellers, so all models are compared
on complete lists.

## Results

*To be added after the run on the full dataset.*

| Model | MAP@12 | Recall@12 |
|---|---:|---:|
| Popularity | | |
| Popular by age band | | |
| Repurchase | | |
| Co-purchase | | |
| Hybrid | | |

## Repository Structure

```
fashion-recommender/
├── data/                       # raw data goes here (not committed) – see data/README.md
├── sql/
│   ├── 00_build_tables.sql     # train/test split, answer key, customer segments
│   └── 01_candidates.sql       # popularity, age band, repurchase, co-purchase candidates
├── src/fashion_recs/
│   ├── db.py                   # DuckDB connection and named-query runner
│   ├── metrics.py              # MAP@12, recall@12
│   └── recommenders.py         # top-12 ranking, score blending, hybrid
├── scripts/
│   ├── make_sample_data.py     # small synthetic dataset for testing
│   ├── build_database.py       # load CSVs into DuckDB and build tables
│   └── run_evaluation.py       # score every model, overall and by segment
└── results/                    # comparison tables written by run_evaluation.py
```

As in the previous project, every SQL query is named (`-- name: repurchase`) and loaded by
name from Python, so the SQL files can also be run directly in the DuckDB CLI.

## How to Run

```bash
pip install -r requirements.txt
# 1. Download the three CSVs into data/raw/ (see data/README.md)
python scripts/build_database.py            # add --customer-pct 20 on a low-memory laptop
python scripts/run_evaluation.py
```

To test the pipeline without the download, `scripts/make_sample_data.py` generates a small
**synthetic** dataset with the same columns (results from it are meaningless):

```bash
python scripts/make_sample_data.py
python scripts/build_database.py --raw-dir data/sample --db data/hm_sample.duckdb
RECS_DB=data/hm_sample.duckdb python scripts/run_evaluation.py
```

## Limitations

- **One test week.** Results come from a single held-out week; a second validation week
  should be used to tune hybrid weights, so the test week is not over-fitted.
- **Purchases only.** There are no clicks, views or returns, so "not bought" doesn't mean
  "not liked".
- **Cold start.** Customers with no history only get popularity-based recommendations.
- **Offline metrics.** MAP@12 measures whether the model predicts purchases, not whether
  recommendations would *cause* extra purchases; that needs an A/B test.
