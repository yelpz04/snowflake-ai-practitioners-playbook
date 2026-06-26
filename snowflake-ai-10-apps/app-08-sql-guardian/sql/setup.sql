-- SQLGuardian Setup SQL — App 8 of 10
CREATE DATABASE IF NOT EXISTS SQLGUARDIAN; CREATE SCHEMA IF NOT EXISTS SQLGUARDIAN.PUBLIC;
USE DATABASE SQLGUARDIAN; USE SCHEMA PUBLIC;

CREATE OR REPLACE TABLE REVIEW_HISTORY (
    REVIEW_ID    STRING DEFAULT UUID_STRING() PRIMARY KEY,
    SQL_HASH     STRING,             -- SHA2 of submitted SQL to detect duplicates
    SUBMITTED_BY STRING DEFAULT CURRENT_USER(),
    RISK_SCORE   INT,
    ISSUE_COUNT  INT,
    HAS_CRITICAL BOOLEAN,
    REVIEW_JSON  VARIANT,            -- full AI JSON response
    REVIEWED_AT  TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- View: weekly risk trend
CREATE OR REPLACE VIEW RISK_TREND AS
SELECT
    DATE_TRUNC('week', REVIEWED_AT) AS week,
    ROUND(AVG(RISK_SCORE), 1)       AS avg_risk_score,
    COUNT(*)                         AS reviews,
    SUM(CASE WHEN HAS_CRITICAL THEN 1 ELSE 0 END) AS critical_reviews,
    SUBMITTED_BY
FROM REVIEW_HISTORY GROUP BY 1, SUBMITTED_BY ORDER BY 1;

-- ── Sample review history (for demo/trend charts without running real reviews) 
INSERT INTO REVIEW_HISTORY (SQL_HASH, SUBMITTED_BY, RISK_SCORE, ISSUE_COUNT, HAS_CRITICAL, REVIEW_JSON, REVIEWED_AT) VALUES
('abc123', 'demo_user', 8, 3, TRUE,
 PARSE_JSON('{"risk_score":8,"summary":"Query scans entire orders table without a WHERE clause — high cost and latency risk.","issues":[{"severity":"CRITICAL","category":"PERFORMANCE","description":"Missing WHERE clause causes full table scan on ORDERS (2.4M rows)","line_hint":"SELECT * FROM orders","recommendation":"Add a date filter: WHERE order_date >= DATEADD(day,-30,CURRENT_DATE())"},{"severity":"WARNING","category":"PERFORMANCE","description":"SELECT * returns all 18 columns — select only what you need","line_hint":"SELECT *","recommendation":"Replace SELECT * with explicit column list"},{"severity":"INFO","category":"STYLE","description":"No LIMIT clause — consider adding LIMIT for exploratory queries","line_hint":"FROM orders","recommendation":"Add LIMIT 1000 for exploration"}],"rewrite":"SELECT order_id, customer_id, order_date, amount FROM orders WHERE order_date >= DATEADD(day,-30,CURRENT_DATE()) LIMIT 1000;"}'),
 DATEADD('day',-14,CURRENT_TIMESTAMP())),
('def456', 'demo_user', 4, 1, FALSE,
 PARSE_JSON('{"risk_score":4,"summary":"Query is mostly correct but uses an implicit type cast that could cause silent errors on non-numeric inputs.","issues":[{"severity":"WARNING","category":"CORRECTNESS","description":"Implicit cast from STRING to FLOAT on AMOUNT column — will error on non-numeric values","line_hint":"SUM(amount)","recommendation":"Use TRY_TO_DOUBLE(amount) to handle nulls and non-numeric values safely"}],"rewrite":"SELECT customer_id, SUM(TRY_TO_DOUBLE(amount)) AS total FROM orders GROUP BY customer_id;"}'),
 DATEADD('day',-7,CURRENT_TIMESTAMP())),
('ghi789', 'demo_user', 2, 1, FALSE,
 PARSE_JSON('{"risk_score":2,"summary":"Well-structured query. Minor style suggestion only.","issues":[{"severity":"INFO","category":"STYLE","description":"Subquery could be rewritten as a CTE for readability","line_hint":"FROM (SELECT ...) sub","recommendation":"Extract the subquery into a WITH clause"}],"rewrite":null}'),
 DATEADD('day',-2,CURRENT_TIMESTAMP()));
