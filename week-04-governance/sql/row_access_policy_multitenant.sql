-- ============================================================
-- Day 18: Multi-Tenant Cortex Agents — Row Access Policy
-- ============================================================
-- Docs: https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-multi-tenancy

USE SCHEMA REVENUE_OPS_AI.RAW;

-- Row access policy using TENANT_ID session variable
CREATE OR REPLACE ROW ACCESS POLICY TENANT_ISOLATION_POLICY
AS (TENANT_ID STRING) RETURNS BOOLEAN ->
    TENANT_ID = CURRENT_SESSION_CONTEXT('TENANT_ID')
    OR IS_ROLE_IN_SESSION('SYSADMIN');

-- Apply to CUSTOMERS table
ALTER TABLE CUSTOMERS ADD ROW ACCESS POLICY TENANT_ISOLATION_POLICY ON (TENANT_ID);

-- Apply to SALES_ORDERS via customer join
-- (For simplicity, add TENANT_ID directly to SALES_ORDERS)
ALTER TABLE SALES_ORDERS ADD COLUMN IF NOT EXISTS TENANT_ID STRING;

UPDATE SALES_ORDERS s
SET TENANT_ID = c.TENANT_ID
FROM CUSTOMERS c
WHERE s.CUSTOMER_ID = c.CUSTOMER_ID;

ALTER TABLE SALES_ORDERS ADD ROW ACCESS POLICY TENANT_ISOLATION_POLICY ON (TENANT_ID);

-- ============================================================
-- Test Tenant Isolation
-- ============================================================

-- Set session context for Tenant A
ALTER SESSION SET TENANT_ID = 'TENANT_A';

-- This should only show Tenant A customers (C001, C002, C005)
SELECT * FROM CUSTOMERS;

-- This should only show Tenant A orders
SELECT * FROM SALES_ORDERS;
