-- ============================================================
-- Day 11: DCM Project — Declarative Table and Task Definitions
-- ============================================================
-- Docs: https://www.snowflake.com/en/blog/declarative-snowflake-pipelines-dcm-projects-cortex-code/

-- These SQL files are referenced by manifest.yml
-- DCM manages them declaratively (analyze → plan → deploy)

-- Daily sales aggregation table
CREATE OR REPLACE TABLE REVENUE_OPS_AI.ANALYTICS.DAILY_SALES_AGG (
    AGG_DATE            DATE            NOT NULL,
    REGION              STRING,
    PRODUCT_CATEGORY    STRING,
    TOTAL_REVENUE       NUMBER(14,2),
    ORDER_COUNT         NUMBER,
    AVG_DISCOUNT        NUMBER(5,2),
    WON_DEALS           NUMBER,
    LOST_DEALS          NUMBER,
    OPEN_DEALS          NUMBER,
    UPDATED_AT          TIMESTAMP_NTZ   DEFAULT CURRENT_TIMESTAMP()
);

-- Customer health snapshot table
CREATE OR REPLACE TABLE REVENUE_OPS_AI.ANALYTICS.CUSTOMER_HEALTH_SNAPSHOT (
    SNAPSHOT_DATE       DATE            NOT NULL,
    CUSTOMER_ID         STRING          NOT NULL,
    CUSTOMER_NAME       STRING,
    HEALTH_STATUS       STRING,
    TOTAL_REVENUE       NUMBER(14,2),
    AVG_RATING          NUMBER(3,1),
    OPEN_TICKETS        NUMBER,
    UPDATED_AT          TIMESTAMP_NTZ   DEFAULT CURRENT_TIMESTAMP()
);
