-- Tables built once from the raw data (run by scripts/build_database.py).
-- Expects the raw tables: transactions, articles, customers.

-- Train / test split: the last 7 days are held out, matching the Kaggle evaluation
-- (predict what each customer buys in the following week).
CREATE OR REPLACE TABLE split AS
SELECT CAST(max(t_dat) - INTERVAL 6 DAY AS DATE) AS test_start,
       max(t_dat)                                AS test_end
FROM transactions;

CREATE OR REPLACE TABLE train AS
SELECT t.*
FROM transactions t CROSS JOIN split s
WHERE t.t_dat < s.test_start;

-- One row per customer who bought anything in the test week: the "answer key".
CREATE OR REPLACE TABLE test_purchases AS
SELECT t.customer_id, list(DISTINCT t.article_id ORDER BY t.article_id) AS articles
FROM transactions t CROSS JOIN split s
WHERE t.t_dat >= s.test_start
GROUP BY t.customer_id;

-- Simple recency / frequency segments at the cutoff date, used to break results down
-- by customer type. Customers with no purchase history are labelled 'New' at evaluation.
CREATE OR REPLACE TABLE customer_segments AS
WITH stats AS (
    SELECT t.customer_id,
           date_diff('day', max(t.t_dat), any_value(s.test_start)) AS recency_days,
           count(DISTINCT t.t_dat)                                AS visits,
           sum(t.price)                                           AS spend
    FROM train t CROSS JOIN split s
    GROUP BY t.customer_id
)
SELECT customer_id, recency_days, visits, spend,
       CASE WHEN recency_days <= 30 AND visits >= 5 THEN 'Champions'
            WHEN recency_days <= 30                 THEN 'Active'
            WHEN recency_days <= 90                 THEN 'Cooling'
            ELSE 'Lapsed' END AS segment
FROM stats;
