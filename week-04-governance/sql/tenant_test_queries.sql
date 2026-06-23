-- ============================================================
-- Day 18: Multi-Tenant Test Queries
-- ============================================================

-- Test as Tenant A
ALTER SESSION SET TENANT_ID = 'TENANT_A';

SELECT 'Tenant A' AS TENANT, COUNT(*) AS CUSTOMER_COUNT FROM CUSTOMERS;
SELECT 'Tenant A' AS TENANT, SUM(TOTAL_AMOUNT) AS TOTAL_REVENUE FROM SALES_ORDERS WHERE DEAL_STAGE = 'Won';

-- Ask the Cortex Agent (via API):
-- "What is my total revenue?" → should see only Tenant A data

-- Test as Tenant B
ALTER SESSION SET TENANT_ID = 'TENANT_B';

SELECT 'Tenant B' AS TENANT, COUNT(*) AS CUSTOMER_COUNT FROM CUSTOMERS;
SELECT 'Tenant B' AS TENANT, SUM(TOTAL_AMOUNT) AS TOTAL_REVENUE FROM SALES_ORDERS WHERE DEAL_STAGE = 'Won';

-- Ask the same question → should see only Tenant B data

-- ============================================================
-- Verify isolation: same question, different answers
-- ============================================================

-- Tenant A sees: C001 (Acme), C002 (Beta), C005 (Epsilon)
-- Tenant B sees: C003 (Gamma), C004 (Delta)

-- The Cortex Agent automatically inherits the session context,
-- so tenant isolation is transparent to the AI.
