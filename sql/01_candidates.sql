-- Candidate generators. Each query returns (customer_id, article_id, score) for the
-- customers in test_purchases; higher score = stronger recommendation.
-- Except for popular_last_week, which returns one global list of (article_id, score).


-- name: popular_last_week
-- The 12 best-selling articles in the final week of training data.
SELECT t.article_id, count(*) AS score
FROM train t CROSS JOIN split s
WHERE t.t_dat >= s.test_start - INTERVAL 7 DAY
GROUP BY t.article_id
ORDER BY score DESC, t.article_id
LIMIT 12;


-- name: popular_by_age_band
-- Last week's best sellers within each 10-year age band.
WITH banded AS (
    SELECT customer_id, coalesce(CAST(floor(age / 10) * 10 AS INTEGER), -1) AS age_band
    FROM customers
),
ranked AS (
    SELECT b.age_band, t.article_id, count(*) AS score,
           row_number() OVER (PARTITION BY b.age_band
                              ORDER BY count(*) DESC, t.article_id) AS rnk
    FROM train t
    JOIN banded b USING (customer_id)
    CROSS JOIN split s
    WHERE t.t_dat >= s.test_start - INTERVAL 7 DAY
    GROUP BY b.age_band, t.article_id
)
SELECT p.customer_id, r.article_id, r.score
FROM test_purchases p
JOIN banded b USING (customer_id)
JOIN ranked r ON r.age_band = b.age_band
WHERE r.rnk <= 12;


-- name: repurchase
-- Articles the customer bought in the last 4 weeks, weighted towards recent purchases.
SELECT t.customer_id, t.article_id,
       sum(1.0 / (1 + date_diff('day', t.t_dat, s.test_start) / 7.0)) AS score
FROM train t CROSS JOIN split s
WHERE t.t_dat >= s.test_start - INTERVAL 28 DAY
  AND t.customer_id IN (SELECT customer_id FROM test_purchases)
GROUP BY t.customer_id, t.article_id;


-- name: co_purchase
-- "Bought together": items that appear in the same basket (customer + day) as items the
-- customer bought recently. Score = sum over their recent items of P(neighbour | item).
WITH baskets AS (
    SELECT DISTINCT t.customer_id, t.t_dat, t.article_id
    FROM train t CROSS JOIN split s
    WHERE t.t_dat >= s.test_start - INTERVAL 56 DAY
),
pairs AS (
    SELECT a.article_id AS item, b.article_id AS neighbour, count(*) AS n
    FROM baskets a
    JOIN baskets b
      ON a.customer_id = b.customer_id
     AND a.t_dat = b.t_dat
     AND a.article_id <> b.article_id
    GROUP BY 1, 2
),
item_counts AS (
    SELECT article_id, count(*) AS n FROM baskets GROUP BY 1
),
neighbours AS (
    SELECT p.item, p.neighbour, p.n / ic.n AS confidence,
           row_number() OVER (PARTITION BY p.item ORDER BY p.n DESC, p.neighbour) AS rnk
    FROM pairs p JOIN item_counts ic ON ic.article_id = p.item
),
history AS (
    SELECT DISTINCT t.customer_id, t.article_id
    FROM train t CROSS JOIN split s
    WHERE t.t_dat >= s.test_start - INTERVAL 28 DAY
      AND t.customer_id IN (SELECT customer_id FROM test_purchases)
)
SELECT h.customer_id, n.neighbour AS article_id, sum(n.confidence) AS score
FROM history h
JOIN neighbours n ON n.item = h.article_id AND n.rnk <= 20
GROUP BY 1, 2;


-- name: test_customers
-- Evaluation targets with their segment ('New' = no purchases before the test week).
SELECT p.customer_id, p.articles, coalesce(cs.segment, 'New') AS segment
FROM test_purchases p
LEFT JOIN customer_segments cs USING (customer_id);
