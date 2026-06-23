-- ============================================================
-- DMF Anomaly Detection
-- ============================================================
-- Docs: https://docs.snowflake.com/en/user-guide/data-quality-anomaly
-- Requires: Enterprise Edition or higher

USE SCHEMA REVENUE_OPS_AI.RAW;

-- ============================================================
-- Enable anomaly detection on DMF results
-- ============================================================

-- Anomaly detection for row count (detects unusual spikes/drops)
ALTER TABLE SALES_ORDERS
  ALTER DATA METRIC FUNCTION SNOWFLAKE.CORE.ROW_COUNT
  SET ANOMALY_DETECTION = TRUE;

ALTER TABLE CUSTOMER_FEEDBACK
  ALTER DATA METRIC FUNCTION SNOWFLAKE.CORE.ROW_COUNT
  SET ANOMALY_DETECTION = TRUE;

-- Anomaly detection for freshness (detects unusual staleness)
ALTER TABLE SALES_ORDERS
  ALTER DATA METRIC FUNCTION SNOWFLAKE.CORE.FRESHNESS
  SET ANOMALY_DETECTION = TRUE;

ALTER TABLE CUSTOMER_FEEDBACK
  ALTER DATA METRIC FUNCTION SNOWFLAKE.CORE.FRESHNESS
  SET ANOMALY_DETECTION = TRUE;

-- ============================================================
-- Query anomaly detection results
-- ============================================================

-- View detected anomalies
SELECT
    TABLE_NAME,
    METRIC_NAME,
    MEASUREMENT_TIME,
    VALUE,
    IS_ANOMALY,
    EXPECTED_RANGE_LOWER,
    EXPECTED_RANGE_UPPER,
    ANOMALY_SCORE
FROM SNOWFLAKE.LOCAL.DATA_QUALITY_MONITORING_RESULTS
WHERE IS_ANOMALY = TRUE
ORDER BY MEASUREMENT_TIME DESC
LIMIT 50;

-- Anomaly trend over time
SELECT
    DATE_TRUNC('day', MEASUREMENT_TIME) AS CHECK_DATE,
    TABLE_NAME,
    METRIC_NAME,
    COUNT(*) AS TOTAL_CHECKS,
    SUM(CASE WHEN IS_ANOMALY THEN 1 ELSE 0 END) AS ANOMALY_COUNT,
    AVG(VALUE) AS AVG_VALUE
FROM SNOWFLAKE.LOCAL.DATA_QUALITY_MONITORING_RESULTS
WHERE MEASUREMENT_TIME > DATEADD('day', -30, CURRENT_TIMESTAMP())
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3;

-- ============================================================
-- Data Quality Manager (DQM) queries
-- ============================================================
-- The Data Quality Manager provides a UI in Snowsight for:
-- - Viewing DMF results across all tables
-- - Setting up alerts for anomalies
-- - Tracking quality trends over time
-- Guide: https://snowflake.com/en/developers/guides/getting-started-with-the-data-quality-manager/

-- Summary: tables with quality issues
SELECT
    TABLE_CATALOG,
    TABLE_SCHEMA,
    TABLE_NAME,
    COUNT(DISTINCT METRIC_NAME) AS METRICS_CONFIGURED,
    SUM(CASE WHEN IS_ANOMALY THEN 1 ELSE 0 END) AS TOTAL_ANOMALIES,
    MAX(MEASUREMENT_TIME) AS LAST_CHECK
FROM SNOWFLAKE.LOCAL.DATA_QUALITY_MONITORING_RESULTS
GROUP BY 1, 2, 3
ORDER BY TOTAL_ANOMALIES DESC;
