-- ============================================================
-- Dynamic Tables ADAPTIVE Refresh (also used in Day 22 Iceberg feature set)
-- ============================================================
-- Docs: https://docs.snowflake.cn/en/release-notes/2026/other/2026-05-26-dynamic-tables-adaptive-refresh-mode
-- ADAPTIVE mode auto-switches between incremental and full refresh

-- Dynamic Table with ADAPTIVE refresh
CREATE OR REPLACE DYNAMIC TABLE REVENUE_OPS_AI.ANALYTICS.DAILY_REVENUE_LIVE
    TARGET_LAG = '30 minutes'
    WAREHOUSE = COMPUTE_WH
    REFRESH_MODE = ADAPTIVE
AS
    SELECT
        ORDER_DATE,
        REGION,
        PRODUCT_CATEGORY,
        SUM(TOTAL_AMOUNT) AS TOTAL_REVENUE,
        COUNT(*) AS ORDER_COUNT,
        AVG(DISCOUNT_PCT) AS AVG_DISCOUNT,
        COUNT(CASE WHEN DEAL_STAGE = 'Won' THEN 1 END) AS WON_DEALS,
        COUNT(CASE WHEN DEAL_STAGE = 'Lost' THEN 1 END) AS LOST_DEALS
    FROM REVENUE_OPS_AI.RAW.SALES_ORDERS
    GROUP BY 1, 2, 3;

-- Why ADAPTIVE?
-- - Normal day: small INSERTs → incremental refresh (fast, cheap)
-- - Bulk load day: INSERT OVERWRITE → auto-detects and does full refresh
-- - After bulk load: resumes incremental refresh
-- No manual intervention needed

-- ============================================================
-- Iceberg + Horizon Catalog
-- ============================================================
-- Docs: https://docs.snowflake.com/en/user-guide/tables-iceberg-query-using-external-query-engine-snowflake-horizon
-- Reference: https://www.snowflake.com/en/blog/engineering/bidirectional-interoperability-iceberg-snowflake-horizon-catalog/

-- Create a Snowflake-managed Iceberg table
CREATE OR REPLACE ICEBERG TABLE REVENUE_OPS_AI.RAW.SALES_ORDERS_ICEBERG (
    ORDER_ID STRING,
    CUSTOMER_ID STRING,
    ORDER_DATE DATE,
    TOTAL_AMOUNT NUMBER(14,2),
    REGION STRING,
    PRODUCT_CATEGORY STRING,
    DEAL_STAGE STRING,
    DISCOUNT_PCT NUMBER(5,2),
    INGESTED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
    CATALOG = 'SNOWFLAKE'
    EXTERNAL_VOLUME = 'my_external_volume'
    BASE_LOCATION = 'revenue_ops/sales_orders/';

-- Bidirectional: External engines (Spark, Trino) can now WRITE to this table
-- via Horizon Catalog's open APIs (Apache Polaris)
-- Snowflake handles: metadata commit, governance, audit trail

-- Single-pane governance across ALL Iceberg tables
-- Whether managed by Snowflake or external catalogs
SELECT TABLE_CATALOG, TABLE_SCHEMA, TABLE_NAME, TABLE_TYPE
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE IN ('BASE TABLE', 'ICEBERG');
