-- ============================================================
-- Day 21: Query Acceleration Service (QAS) Test Queries
-- ============================================================
-- Docs: https://www.snowflake.com/en/blog/engineering/query-acceleration-service-enabled-by-default/
-- QAS is now enabled by default on warehouses.

-- Check if QAS is enabled on your warehouse
SHOW WAREHOUSES LIKE 'COMPUTE_WH';

-- Check QAS eligibility for recent queries
SELECT
    QUERY_ID,
    QUERY_TEXT,
    TOTAL_ELAPSED_TIME / 1000 AS ELAPSED_SECONDS,
    QUERY_ACCELERATION_UPPER_LIMIT_SCALE_FACTOR,
    ELIGIBLE_QUERY_ACCELERATION_MAX_SCALE_FACTOR
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE START_TIME > DATEADD('hour', -24, CURRENT_TIMESTAMP())
  AND ELIGIBLE_QUERY_ACCELERATION_MAX_SCALE_FACTOR > 0
ORDER BY TOTAL_ELAPSED_TIME DESC
LIMIT 20;

-- Heavy analytical query to test QAS impact
-- (Run this query before and after enabling QAS to compare)
SELECT
    s.REGION,
    s.PRODUCT_CATEGORY,
    c.INDUSTRY,
    c.COMPANY_SIZE,
    DATE_TRUNC('month', s.ORDER_DATE) AS ORDER_MONTH,
    COUNT(DISTINCT s.ORDER_ID) AS ORDER_COUNT,
    COUNT(DISTINCT s.CUSTOMER_ID) AS UNIQUE_CUSTOMERS,
    SUM(s.TOTAL_AMOUNT) AS TOTAL_REVENUE,
    AVG(s.DISCOUNT_PCT) AS AVG_DISCOUNT,
    SUM(CASE WHEN s.DEAL_STAGE = 'Won' THEN s.TOTAL_AMOUNT ELSE 0 END) AS WON_REVENUE,
    SUM(CASE WHEN s.DEAL_STAGE = 'Lost' THEN s.TOTAL_AMOUNT ELSE 0 END) AS LOST_REVENUE,
    COUNT(CASE WHEN s.DEAL_STAGE = 'Won' THEN 1 END)::FLOAT /
        NULLIF(COUNT(CASE WHEN s.DEAL_STAGE IN ('Won', 'Lost') THEN 1 END), 0) AS WIN_RATE
FROM REVENUE_OPS_AI.RAW.SALES_ORDERS s
JOIN REVENUE_OPS_AI.RAW.CUSTOMERS c ON s.CUSTOMER_ID = c.CUSTOMER_ID
GROUP BY 1, 2, 3, 4, 5
ORDER BY TOTAL_REVENUE DESC;

-- Query profile analysis
-- After running the query, check the query profile in Snowsight:
-- 1. Look for "Query Acceleration" in the profile
-- 2. Note the scale factor used
-- 3. Compare elapsed time with/without QAS
