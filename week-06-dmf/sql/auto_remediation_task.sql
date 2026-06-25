-- ============================================================
-- Autonomous Remediation Task — Self-Healing Data Pipeline
-- ============================================================
-- Docs: https://docs.snowflake.com/en/user-guide/tasks-intro
-- Requires: EXECUTE TASK privilege on the warehouse

USE DATABASE REVENUE_OPS_AI;
USE SCHEMA ANALYTICS;

-- ============================================================
-- DQ Baselines — rolling 30-day statistics per metric
-- ============================================================

CREATE OR REPLACE TABLE ANALYTICS.DQ_BASELINES AS
SELECT
    TABLE_NAME,
    METRIC_NAME,
    AVG(VALUE)                   AS baseline_avg,
    STDDEV(VALUE)                AS baseline_stddev,
    PERCENTILE_CONT(0.1) WITHIN GROUP (ORDER BY VALUE) AS p10,
    PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY VALUE) AS p90,
    MIN(VALUE)                   AS historical_min,
    MAX(VALUE)                   AS historical_max,
    COUNT(*)                     AS sample_size
FROM SNOWFLAKE.LOCAL.DATA_QUALITY_MONITORING_RESULTS
WHERE MEASUREMENT_TIME >= DATEADD('day', -30, CURRENT_TIMESTAMP())
GROUP BY TABLE_NAME, METRIC_NAME;

-- ============================================================
-- DQ Anomalies — statistical outlier detection (z-score)
-- ============================================================

CREATE OR REPLACE TABLE ANALYTICS.DQ_ANOMALIES AS
SELECT
    r.MEASUREMENT_TIME,
    r.TABLE_NAME,
    r.METRIC_NAME,
    r.VALUE                                              AS current_value,
    b.baseline_avg,
    b.baseline_stddev,
    ABS(r.VALUE - b.baseline_avg) / NULLIF(b.baseline_stddev, 0) AS z_score,
    CASE
        WHEN ABS(r.VALUE - b.baseline_avg) / NULLIF(b.baseline_stddev, 0) > 3 THEN 'CRITICAL'
        WHEN ABS(r.VALUE - b.baseline_avg) / NULLIF(b.baseline_stddev, 0) > 2 THEN 'WARNING'
        ELSE 'NORMAL'
    END AS anomaly_level,
    SNOWFLAKE.CORTEX.COMPLETE(
        'claude-haiku-4-5',
        'In one sentence, describe this data quality anomaly:
         Table: ' || r.TABLE_NAME || '
         Metric: ' || r.METRIC_NAME || '
         Current value: ' || r.VALUE || '
         Normal range: ' || b.p10 || ' to ' || b.p90 || '
         Z-score: ' || ROUND(ABS(r.VALUE - b.baseline_avg) / NULLIF(b.baseline_stddev, 0), 1)
    ) AS anomaly_description
FROM SNOWFLAKE.LOCAL.DATA_QUALITY_MONITORING_RESULTS r
JOIN DQ_BASELINES b
    ON r.TABLE_NAME = b.TABLE_NAME AND r.METRIC_NAME = b.METRIC_NAME
WHERE r.MEASUREMENT_TIME >= DATEADD('hour', -2, CURRENT_TIMESTAMP())
  AND ABS(r.VALUE - b.baseline_avg) / NULLIF(b.baseline_stddev, 0) > 2;

-- ============================================================
-- Remediation Log — audit trail for all AI-suggested fixes
-- ============================================================

CREATE OR REPLACE TABLE ANALYTICS.REMEDIATION_LOG (
    LOG_ID               STRING DEFAULT UUID_STRING(),
    LOGGED_AT            TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    ANOMALY_COUNT        INTEGER,
    SUGGESTED_REMEDIATION STRING,
    EXECUTED             BOOLEAN DEFAULT FALSE,
    EXECUTED_AT          TIMESTAMP_NTZ,
    EXECUTION_RESULT     STRING
);

-- ============================================================
-- Autonomous Remediation Task
-- Runs every 15 minutes — detects critical anomalies,
-- asks CoCo to suggest a safe remediation query, logs it.
-- Execution requires human approval unless EXECUTED is auto-set.
-- ============================================================

CREATE OR REPLACE TASK REVENUE_OPS_AI.RAW.AUTO_REMEDIATION_TASK
    WAREHOUSE = REVOPS_AI_WH
    SCHEDULE = '15 MINUTE'
AS
DECLARE
    anomaly_count INTEGER;
    remediation_sql STRING;
BEGIN
    SELECT COUNT(*) INTO :anomaly_count
    FROM ANALYTICS.DQ_ANOMALIES
    WHERE anomaly_level = 'CRITICAL'
      AND MEASUREMENT_TIME >= DATEADD('minute', -20, CURRENT_TIMESTAMP());

    IF (:anomaly_count > 0) THEN
        SELECT SNOWFLAKE.CORTEX.COMPLETE(
            'claude-sonnet-4-6',
            'You are a Snowflake data engineer. A data quality anomaly has been detected.
             Generate a SQL query to investigate and if safe, fix the issue.
             Only generate SELECT or INSERT statements — no DROP, DELETE, or DDL.
             Return only the SQL with a brief comment explaining what it does.

             Anomaly details: ' || (
                 SELECT ARRAY_TO_STRING(ARRAY_AGG(
                     TABLE_NAME || ': ' || anomaly_description
                 ), '; ')
                 FROM ANALYTICS.DQ_ANOMALIES
                 WHERE anomaly_level = 'CRITICAL'
                   AND MEASUREMENT_TIME >= DATEADD('minute', -20, CURRENT_TIMESTAMP())
             )
        ) INTO :remediation_sql;

        INSERT INTO ANALYTICS.REMEDIATION_LOG
            (LOGGED_AT, ANOMALY_COUNT, SUGGESTED_REMEDIATION)
        VALUES (CURRENT_TIMESTAMP(), :anomaly_count, :remediation_sql);
    END IF;
END;

-- Activate the task
ALTER TASK AUTO_REMEDIATION_TASK RESUME;
