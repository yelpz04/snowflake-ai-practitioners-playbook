-- ============================================================
-- Virtual Columns in Data Model
-- ============================================================
-- Docs: https://docs.snowflake.com/en/sql-reference/virtual-columns
-- Virtual columns are computed at query time, zero storage cost

-- Add virtual columns to existing tables
ALTER TABLE REVENUE_OPS_AI.RAW.SALES_ORDERS ADD COLUMN
    REVENUE_CATEGORY STRING AS (
        CASE
            WHEN TOTAL_AMOUNT >= 50000 THEN 'Enterprise'
            WHEN TOTAL_AMOUNT >= 10000 THEN 'Mid-Market'
            ELSE 'SMB'
        END
    );

ALTER TABLE REVENUE_OPS_AI.RAW.SALES_ORDERS ADD COLUMN
    DEAL_VALUE_TIER STRING AS (
        CASE
            WHEN DISCOUNT_PCT > 20 THEN 'Heavy Discount'
            WHEN DISCOUNT_PCT > 10 THEN 'Moderate Discount'
            WHEN DISCOUNT_PCT > 0 THEN 'Light Discount'
            ELSE 'Full Price'
        END
    );

-- Customer health virtual column
ALTER TABLE REVENUE_OPS_AI.RAW.CUSTOMERS ADD COLUMN
    SEGMENT_LABEL STRING AS (
        UPPER(COMPANY_SIZE) || ' - ' || UPPER(INDUSTRY)
    );

-- Verify virtual columns
DESC TABLE REVENUE_OPS_AI.RAW.SALES_ORDERS;
-- Look for KIND = 'VIRTUAL' in the output
