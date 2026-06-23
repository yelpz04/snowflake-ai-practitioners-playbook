-- ============================================================
-- Agent Usage Dashboard Queries
-- ============================================================
-- For Observe by Snowflake and general observability

-- ============================================================
-- 1. Cortex Agent API usage
-- ============================================================
SELECT
    DATE_TRUNC('hour', START_TIME) AS USAGE_HOUR,
    USER_NAME,
    COUNT(*) AS API_CALLS,
    AVG(TOTAL_ELAPSED_TIME) / 1000 AS AVG_ELAPSED_SECONDS,
    SUM(CREDITS_USED_CLOUD_SERVICES) AS CLOUD_CREDITS
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE QUERY_TAG LIKE '%cortex_agent%'
   OR QUERY_TEXT ILIKE '%CORTEX.AI_COMPLETE%'
   OR QUERY_TEXT ILIKE '%CORTEX.AGENT%'
AND START_TIME > DATEADD('day', -7, CURRENT_TIMESTAMP())
GROUP BY 1, 2
ORDER BY 1 DESC;

-- ============================================================
-- 2. Warehouse utilization during AI workloads
-- ============================================================
SELECT
    START_TIME,
    END_TIME,
    WAREHOUSE_NAME,
    CREDITS_USED,
    CREDITS_USED_COMPUTE,
    CREDITS_USED_CLOUD_SERVICES,
    AVG_RUNNING,
    AVG_QUEUED_LOAD
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE START_TIME > DATEADD('day', -7, CURRENT_TIMESTAMP())
ORDER BY START_TIME DESC;

-- ============================================================
-- 3. Data freshness check (for observability)
-- ============================================================
SELECT
    TABLE_CATALOG,
    TABLE_SCHEMA,
    TABLE_NAME,
    ROW_COUNT,
    BYTES,
    LAST_ALTERED,
    DATEDIFF('hour', LAST_ALTERED, CURRENT_TIMESTAMP()) AS HOURS_SINCE_UPDATE,
    CASE
        WHEN DATEDIFF('hour', LAST_ALTERED, CURRENT_TIMESTAMP()) < 24 THEN 'Fresh'
        WHEN DATEDIFF('hour', LAST_ALTERED, CURRENT_TIMESTAMP()) < 72 THEN 'Stale'
        ELSE 'Critical'
    END AS FRESHNESS_STATUS
FROM SNOWFLAKE.ACCOUNT_USAGE.TABLES
WHERE TABLE_CATALOG = 'REVENUE_OPS_AI'
  AND DELETED IS NULL
ORDER BY HOURS_SINCE_UPDATE DESC;

-- ============================================================
-- 4. Error rate tracking
-- ============================================================
SELECT
    DATE_TRUNC('day', START_TIME) AS ERROR_DATE,
    ERROR_CODE,
    ERROR_MESSAGE,
    COUNT(*) AS ERROR_COUNT
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE START_TIME > DATEADD('day', -30, CURRENT_TIMESTAMP())
  AND ERROR_CODE IS NOT NULL
  AND DATABASE_NAME = 'REVENUE_OPS_AI'
GROUP BY 1, 2, 3
ORDER BY ERROR_COUNT DESC;
