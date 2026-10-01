"""Ranking metrics. MAP@12 follows the H&M Kaggle competition definition."""
import numpy as np


def average_precision_at_k(actual, predicted, k=12):
    """AP@k for one customer: precision at each hit, averaged over min(len(actual), k)."""
    if not actual:
        return 0.0
    actual = set(actual)
    hits, score = 0, 0.0
    for i, item in enumerate(predicted[:k], start=1):
        if item in actual and item not in predicted[: i - 1]:
            hits += 1
            score += hits / i
    return score / min(len(actual), k)


def recall_at_k(actual, predicted, k=12):
    if not actual:
        return 0.0
    return len(set(actual) & set(predicted[:k])) / len(set(actual))


def evaluate(actual: dict, predicted: dict, k=12) -> dict:
    """Score predictions for every customer in `actual` (missing predictions score 0)."""
    ap = [average_precision_at_k(a, predicted.get(c, []), k) for c, a in actual.items()]
    rec = [recall_at_k(a, predicted.get(c, []), k) for c, a in actual.items()]
    return {f"map@{k}": float(np.mean(ap)), f"recall@{k}": float(np.mean(rec))}


def per_customer_ap(actual: dict, predicted: dict, k=12) -> dict:
    return {c: average_precision_at_k(a, predicted.get(c, []), k) for c, a in actual.items()}
