-- ============================================================
-- Semantic Views for Business-Friendly Agent Answers
-- ============================================================
-- Docs: https://docs.snowflake.com/en/user-guide/views-semantic/overview

USE SCHEMA REVENUE_OPS_AI.ANALYTICS;

-- Create a semantic view over sales data
CREATE OR REPLACE SEMANTIC VIEW SALES_METRICS_SV
  COMMENT = 'Business-friendly sales metrics for natural language queries via Cortex Agent'
AS
  -- Logical tables
  TABLES (
    ORDERS AS (
      SELECT
        ORDER_ID,
        CUSTOMER_ID,
        ORDER_DATE,
        PRODUCT_CATEGORY,
        PRODUCT_NAME,
        QUANTITY,
        UNIT_PRICE,
        DISCOUNT_PCT,
        TOTAL_AMOUNT,
        REGION,
        SALES_REP,
        DEAL_STAGE
      FROM REVENUE_OPS_AI.RAW.SALES_ORDERS
    )
      PRIMARY KEY (ORDER_ID)
      COMMENT = 'All sales orders across regions and product categories',

    CUSTOMERS AS (
      SELECT
        CUSTOMER_ID,
        CUSTOMER_NAME,
        INDUSTRY,
        COMPANY_SIZE,
        REGION,
        COUNTRY
      FROM REVENUE_OPS_AI.RAW.CUSTOMERS
    )
      PRIMARY KEY (CUSTOMER_ID)
      COMMENT = 'Customer master data with segmentation attributes'
  )
  -- Relationships
  RELATIONSHIPS (
    ORDERS (CUSTOMER_ID) REFERENCES CUSTOMERS (CUSTOMER_ID)
      COMMENT = 'Each order belongs to one customer'
  )
  -- Metrics
  METRICS (
    TOTAL_REVENUE AS (
      SELECT SUM(TOTAL_AMOUNT) FROM ORDERS WHERE DEAL_STAGE = 'Won'
    )
      COMMENT = 'Total revenue from won deals only',

    AVG_DEAL_SIZE AS (
      SELECT AVG(TOTAL_AMOUNT) FROM ORDERS WHERE DEAL_STAGE = 'Won'
    )
      COMMENT = 'Average deal size for won orders',

    AVG_DISCOUNT AS (
      SELECT AVG(DISCOUNT_PCT) FROM ORDERS
    )
      COMMENT = 'Average discount percentage across all orders',

    WIN_RATE AS (
      SELECT
        COUNT(CASE WHEN DEAL_STAGE = 'Won' THEN 1 END)::FLOAT /
        NULLIF(COUNT(CASE WHEN DEAL_STAGE IN ('Won', 'Lost') THEN 1 END), 0)
      FROM ORDERS
    )
      COMMENT = 'Ratio of won deals to total closed deals (won + lost)',

    ORDER_COUNT AS (
      SELECT COUNT(*) FROM ORDERS
    )
      COMMENT = 'Total number of orders regardless of stage'
  );

-- Verify the semantic view
DESCRIBE SEMANTIC VIEW SALES_METRICS_SV;

-- Test a query against the semantic view
-- (In practice, the Cortex Agent uses this automatically)
SELECT * FROM TABLE(
  SNOWFLAKE.CORTEX.SEMANTIC_VIEW_QUERY(
    'REVENUE_OPS_AI.ANALYTICS.SALES_METRICS_SV',
    'What is the total revenue by region?'
  )
);
