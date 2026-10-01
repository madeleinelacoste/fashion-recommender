"""Turn candidate scores into ranked top-12 lists, and blend recommenders into a hybrid.

Every recommender's output is filled up to 12 items with last week's global best
sellers, so each model is compared on a full list.
"""
import pandas as pd

from .db import query

K = 12
CANDIDATE_QUERIES = ["popular_by_age_band", "repurchase", "co_purchase"]


def top_k(candidates: pd.DataFrame, fallback: list, k=K) -> dict:
    """{customer_id: [article_id, ...]} from (customer_id, article_id, score) rows."""
    ranked = (candidates.sort_values(["customer_id", "score", "article_id"],
                                     ascending=[True, False, True])
                        .groupby("customer_id")["article_id"].agg(list))
    recs = {}
    for customer, items in ranked.items():
        items = items[:k]
        recs[customer] = items + [a for a in fallback if a not in items][: k - len(items)]
    return recs


def fill_missing(recs: dict, customers, fallback: list) -> dict:
    """Customers with no candidates get the fallback list."""
    return {c: recs.get(c, fallback[:K]) for c in customers}


def normalise(candidates: pd.DataFrame) -> pd.DataFrame:
    """Scale scores to 0-1 within each customer so recommenders can be blended."""
    out = candidates.copy()
    out["score"] = out["score"] / out.groupby("customer_id")["score"].transform("max")
    return out


def blend(candidate_sets: dict, weights: dict) -> pd.DataFrame:
    """Weighted sum of normalised scores across recommenders."""
    parts = [normalise(candidate_sets[name]).assign(score=lambda d, w=w: d["score"] * w)
             for name, w in weights.items() if w]
    return (pd.concat(parts)
              .groupby(["customer_id", "article_id"], as_index=False)["score"].sum())


def load_candidates(con) -> tuple[list, dict]:
    """Global popularity list plus each candidate generator's output."""
    popular = query(con, "popular_last_week")["article_id"].tolist()
    return popular, {name: query(con, name) for name in CANDIDATE_QUERIES}


def build_all(con, customers, weights: dict) -> dict:
    """{model_name: {customer_id: [12 articles]}} for every baseline plus the hybrid."""
    popular, cands = load_candidates(con)
    models = {"popularity": {c: popular[:K] for c in customers}}
    for name, df in cands.items():
        models[name] = fill_missing(top_k(df, popular), customers, popular)
    models["hybrid"] = fill_missing(top_k(blend(cands, weights), popular), customers, popular)
    return models
