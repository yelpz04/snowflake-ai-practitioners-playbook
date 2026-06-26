-- ============================================================
-- SnowCost AI — Setup SQL
-- App 1 of 10: Cortex Analyst + AI_COMPLETE + Account Usage
-- ============================================================
-- Run as ACCOUNTADMIN or a role with MONITOR USAGE privilege
-- Docs: https://docs.snowflake.com/en/user-guide/cortex-analyst

-- 1. Database + schema
CREATE DATABASE IF NOT EXISTS SNOWCOST_AI;
CREATE SCHEMA  IF NOT EXISTS SNOWCOST_AI.PUBLIC;

USE DATABASE SNOWCOST_AI;
USE SCHEMA    PUBLIC;

-- 2. Semantic View for Cortex Analyst
--    Cortex Analyst queries this — not raw ACCOUNT_USAGE tables directly
CREATE OR REPLACE SEMANTIC VIEW SNOWCOST_AI_SV
  COMMENT = 'Business-friendly cost view for Cortex Analyst natural language queries'
  TABLES (
    TABLE SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY AS WAREHOUSE_COSTS
      PRIMARY KEY (WAREHOUSE_ID)
      COMMENT = 'Hourly credit consumption per warehouse'
  )
  DIMENSIONS (
    WAREHOUSE_COSTS.WAREHOUSE_NAME
      COMMENT = 'Name of the Snowflake virtual warehouse',
    WAREHOUSE_COSTS.START_TIME
      COMMENT = 'Hour the metering window started (UTC)',
    WAREHOUSE_COSTS.WAREHOUSE_TYPE
      COMMENT = 'Warehouse type: Standard, Snowpark-Optimized, etc.'
  )
  METRICS (
    MEASURE WAREHOUSE_COSTS.CREDITS_USED
      COMMENT = 'Total credits consumed this hour (compute + cloud services). 1 credit = approx $2-4 USD.'
      DEFAULT AGGREGATION = SUM,
    MEASURE WAREHOUSE_COSTS.CREDITS_USED_COMPUTE
      COMMENT = 'Credits used for compute only',
    MEASURE WAREHOUSE_COSTS.CREDITS_USED_CLOUD_SERVICES
      COMMENT = 'Credits used for cloud services (metadata, auth, compilation)'
  );

-- 3. Pre-built cost summary view (used by anomaly detection in the app)
CREATE OR REPLACE VIEW DAILY_WAREHOUSE_COSTS AS
SELECT
    DATE_TRUNC('day', START_TIME)                AS cost_date,
    WAREHOUSE_NAME,
    WAREHOUSE_TYPE,
    SUM(CREDITS_USED)                            AS total_credits,
    SUM(CREDITS_USED_COMPUTE)                    AS compute_credits,
    SUM(CREDITS_USED_CLOUD_SERVICES)             AS cloud_service_credits
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE START_TIME >= DATEADD('day', -90, CURRENT_TIMESTAMP())
GROUP BY 1, 2, 3;

-- 4. Rolling 30-day baseline + z-score anomaly detection
CREATE OR REPLACE VIEW COST_ANOMALIES AS
WITH baseline AS (
    SELECT
        WAREHOUSE_NAME,
        AVG(total_credits)    AS avg_credits,
        STDDEV(total_credits) AS stddev_credits
    FROM DAILY_WAREHOUSE_COSTS
    WHERE cost_date >= DATEADD('day', -30, CURRENT_DATE())
    GROUP BY WAREHOUSE_NAME
),
recent AS (
    SELECT * FROM DAILY_WAREHOUSE_COSTS
    WHERE cost_date >= DATEADD('day', -7, CURRENT_DATE())
)
SELECT
    r.cost_date,
    r.WAREHOUSE_NAME,
    r.total_credits,
    b.avg_credits,
    b.stddev_credits,
    ROUND(ABS(r.total_credits - b.avg_credits) / NULLIF(b.stddev_credits, 0), 2) AS z_score,
    CASE
        WHEN ABS(r.total_credits - b.avg_credits) / NULLIF(b.stddev_credits, 0) > 3 THEN 'CRITICAL'
        WHEN ABS(r.total_credits - b.avg_credits) / NULLIF(b.stddev_credits, 0) > 2 THEN 'WARNING'
        ELSE 'NORMAL'
    END AS anomaly_level
FROM recent r
JOIN baseline b USING (WAREHOUSE_NAME)
WHERE ABS(r.total_credits - b.avg_credits) / NULLIF(b.stddev_credits, 0) > 2
ORDER BY z_score DESC;

-- 5. Resource monitor recommendations view
CREATE OR REPLACE VIEW RESOURCE_MONITOR_GAPS AS
SELECT
    W.NAME                                         AS warehouse_name,
    W.SIZE                                         AS warehouse_size,
    W.AUTO_SUSPEND                                 AS auto_suspend_seconds,
    RM.NAME                                        AS resource_monitor,
    CASE WHEN RM.NAME IS NULL THEN 'NO MONITOR'
         ELSE 'MONITORED' END                      AS monitor_status
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSES W
LEFT JOIN SNOWFLAKE.ACCOUNT_USAGE.RESOURCE_MONITORS RM
    ON W.RESOURCE_MONITOR = RM.NAME
WHERE W.DELETED IS NULL;

-- 6. Demo / mock data — mirrors WAREHOUSE_METERING_HISTORY for accounts
--    without ACCOUNT_USAGE access (e.g., trial accounts, sandboxes).
--    Skip this block in production — DAILY_WAREHOUSE_COSTS reads live data.
CREATE OR REPLACE TABLE DEMO_METERING_HISTORY (
    WAREHOUSE_ID   INT, WAREHOUSE_NAME STRING, WAREHOUSE_TYPE STRING,
    START_TIME     TIMESTAMP_NTZ, END_TIME TIMESTAMP_NTZ,
    CREDITS_USED   FLOAT, CREDITS_USED_COMPUTE FLOAT, CREDITS_USED_CLOUD_SERVICES FLOAT
);
INSERT INTO DEMO_METERING_HISTORY (WAREHOUSE_ID, WAREHOUSE_NAME, WAREHOUSE_TYPE, START_TIME, END_TIME, CREDITS_USED, CREDITS_USED_COMPUTE, CREDITS_USED_CLOUD_SERVICES) VALUES
(1, 'COMPUTE_WH',   'Standard', DATEADD('day',-1,CURRENT_DATE()), DATEADD('hour',-23,CURRENT_DATE()), 1.2,  1.0,  0.2),
(1, 'COMPUTE_WH',   'Standard', DATEADD('day',-2,CURRENT_DATE()), DATEADD('hour',-47,CURRENT_DATE()), 0.8,  0.7,  0.1),
(1, 'COMPUTE_WH',   'Standard', DATEADD('day',-3,CURRENT_DATE()), DATEADD('hour',-71,CURRENT_DATE()), 9.5,  9.0,  0.5),  -- spike
(2, 'ANALYTICS_WH', 'Standard', DATEADD('day',-1,CURRENT_DATE()), DATEADD('hour',-23,CURRENT_DATE()), 3.4,  3.2,  0.2),
(2, 'ANALYTICS_WH', 'Standard', DATEADD('day',-2,CURRENT_DATE()), DATEADD('hour',-47,CURRENT_DATE()), 3.1,  2.9,  0.2),
(2, 'ANALYTICS_WH', 'Standard', DATEADD('day',-3,CURRENT_DATE()), DATEADD('hour',-71,CURRENT_DATE()), 3.3,  3.1,  0.2),
(3, 'ML_WH',        'Snowpark-Optimized', DATEADD('day',-1,CURRENT_DATE()), DATEADD('hour',-23,CURRENT_DATE()), 5.0, 4.8, 0.2),
(3, 'ML_WH',        'Snowpark-Optimized', DATEADD('day',-4,CURRENT_DATE()), DATEADD('hour',-95,CURRENT_DATE()), 22.0, 21.5, 0.5); -- large spike

-- 7. Grant to app role (adjust role name as needed)
GRANT USAGE  ON DATABASE  SNOWCOST_AI TO ROLE SYSADMIN;
GRANT USAGE  ON SCHEMA    SNOWCOST_AI.PUBLIC TO ROLE SYSADMIN;
GRANT SELECT ON ALL VIEWS IN SCHEMA SNOWCOST_AI.PUBLIC TO ROLE SYSADMIN;
GRANT USAGE  ON SEMANTIC VIEW SNOWCOST_AI.PUBLIC.SNOWCOST_AI_SV TO ROLE SYSADMIN;
