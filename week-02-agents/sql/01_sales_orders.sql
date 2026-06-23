-- ============================================================
-- Day 6: Sales Orders + Customers for Cortex Agent
-- ============================================================
-- Tables already created in Week 1 (01_create_feedback_tables.sql)
-- This file adds additional data and views for the agent.

USE SCHEMA REVENUE_OPS_AI.ANALYTICS;

-- Aggregated sales view for the agent
CREATE OR REPLACE VIEW SALES_SUMMARY AS
SELECT
    s.REGION,
    s.PRODUCT_CATEGORY,
    s.SALES_REP,
    c.INDUSTRY,
    c.COMPANY_SIZE,
    s.DEAL_STAGE,
    COUNT(*)                                AS ORDER_COUNT,
    SUM(s.TOTAL_AMOUNT)                    AS TOTAL_REVENUE,
    AVG(s.DISCOUNT_PCT)                    AS AVG_DISCOUNT,
    AVG(s.TOTAL_AMOUNT)                    AS AVG_DEAL_SIZE,
    MIN(s.ORDER_DATE)                      AS FIRST_ORDER_DATE,
    MAX(s.ORDER_DATE)                      AS LAST_ORDER_DATE
FROM REVENUE_OPS_AI.RAW.SALES_ORDERS s
JOIN REVENUE_OPS_AI.RAW.CUSTOMERS c ON s.CUSTOMER_ID = c.CUSTOMER_ID
GROUP BY 1, 2, 3, 4, 5, 6;

-- Customer health view (feedback + tickets + revenue)
CREATE OR REPLACE VIEW CUSTOMER_HEALTH AS
SELECT
    c.CUSTOMER_ID,
    c.CUSTOMER_NAME,
    c.INDUSTRY,
    c.REGION,
    c.COMPANY_SIZE,
    COALESCE(rev.TOTAL_REVENUE, 0)         AS TOTAL_REVENUE,
    COALESCE(rev.ORDER_COUNT, 0)           AS ORDER_COUNT,
    COALESCE(fb.AVG_RATING, 0)             AS AVG_FEEDBACK_RATING,
    COALESCE(fb.FEEDBACK_COUNT, 0)         AS FEEDBACK_COUNT,
    COALESCE(tkt.OPEN_TICKETS, 0)          AS OPEN_TICKETS,
    COALESCE(tkt.TOTAL_TICKETS, 0)         AS TOTAL_TICKETS,
    CASE
        WHEN fb.AVG_RATING < 2.5 AND tkt.OPEN_TICKETS > 0 THEN 'At Risk'
        WHEN fb.AVG_RATING < 3.5 THEN 'Needs Attention'
        WHEN fb.AVG_RATING >= 4.0 AND tkt.OPEN_TICKETS = 0 THEN 'Healthy'
        ELSE 'Monitor'
    END AS HEALTH_STATUS
FROM REVENUE_OPS_AI.RAW.CUSTOMERS c
LEFT JOIN (
    SELECT CUSTOMER_ID, SUM(TOTAL_AMOUNT) AS TOTAL_REVENUE, COUNT(*) AS ORDER_COUNT
    FROM REVENUE_OPS_AI.RAW.SALES_ORDERS WHERE DEAL_STAGE = 'Won'
    GROUP BY 1
) rev ON c.CUSTOMER_ID = rev.CUSTOMER_ID
LEFT JOIN (
    SELECT CUSTOMER_ID, AVG(RATING) AS AVG_RATING, COUNT(*) AS FEEDBACK_COUNT
    FROM REVENUE_OPS_AI.RAW.CUSTOMER_FEEDBACK
    GROUP BY 1
) fb ON c.CUSTOMER_ID = fb.CUSTOMER_ID
LEFT JOIN (
    SELECT CUSTOMER_ID,
           COUNT(CASE WHEN STATUS IN ('Open', 'In Progress') THEN 1 END) AS OPEN_TICKETS,
           COUNT(*) AS TOTAL_TICKETS
    FROM REVENUE_OPS_AI.RAW.SUPPORT_TICKETS
    GROUP BY 1
) tkt ON c.CUSTOMER_ID = tkt.CUSTOMER_ID;

-- Add more sample data for richer agent demos
INSERT INTO REVENUE_OPS_AI.RAW.SALES_ORDERS VALUES
('ORD007', 'C002', '2025-07-10', 'Software',  'Analytics Module',  2, 8000.00,  5.00,  15200.00, 'EMEA',          'Bob',   'Won',  CURRENT_TIMESTAMP()),
('ORD008', 'C003', '2025-08-15', 'Hardware',  'Edge Devices',      20, 1500.00, 12.00, 26400.00, 'APAC',          'Carol', 'Won',  CURRENT_TIMESTAMP()),
('ORD009', 'C001', '2025-09-01', 'Services',  'Training',          10, 500.00,   0.00,  5000.00, 'North America', 'Alice', 'Open', CURRENT_TIMESTAMP()),
('ORD010', 'C005', '2025-10-20', 'Hardware',  'Networking Gear',    5, 4000.00, 15.00, 17000.00, 'EMEA',          'Eve',   'Lost', CURRENT_TIMESTAMP());
