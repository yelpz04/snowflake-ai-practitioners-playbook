-- ============================================================
-- Create base tables for the Revenue Ops Assistant
-- ============================================================

USE ROLE SYSADMIN;
CREATE DATABASE IF NOT EXISTS REVENUE_OPS_AI;
CREATE SCHEMA IF NOT EXISTS REVENUE_OPS_AI.RAW;
CREATE SCHEMA IF NOT EXISTS REVENUE_OPS_AI.ANALYTICS;
CREATE SCHEMA IF NOT EXISTS REVENUE_OPS_AI.AI_OUTPUTS;

USE SCHEMA REVENUE_OPS_AI.RAW;

-- Customer feedback table
CREATE OR REPLACE TABLE CUSTOMER_FEEDBACK (
    FEEDBACK_ID         STRING      NOT NULL,
    CUSTOMER_ID         STRING      NOT NULL,
    FEEDBACK_DATE       TIMESTAMP   NOT NULL,
    CHANNEL             STRING,         -- email, chat, call, survey
    FEEDBACK_TEXT       STRING,
    RATING              NUMBER(2,1),    -- 1.0 to 5.0
    PRODUCT_LINE        STRING,
    REGION              STRING,
    INGESTED_AT         TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Sales orders table
CREATE OR REPLACE TABLE SALES_ORDERS (
    ORDER_ID            STRING      NOT NULL,
    CUSTOMER_ID         STRING      NOT NULL,
    ORDER_DATE          DATE        NOT NULL,
    PRODUCT_CATEGORY    STRING,         -- Hardware, Software, Services
    PRODUCT_NAME        STRING,
    QUANTITY            NUMBER,
    UNIT_PRICE          NUMBER(12,2),
    DISCOUNT_PCT        NUMBER(5,2),
    TOTAL_AMOUNT        NUMBER(14,2),
    REGION              STRING,
    SALES_REP           STRING,
    DEAL_STAGE          STRING,         -- Won, Lost, Open
    INGESTED_AT         TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Customers dimension
CREATE OR REPLACE TABLE CUSTOMERS (
    CUSTOMER_ID         STRING      NOT NULL,
    CUSTOMER_NAME       STRING,
    INDUSTRY            STRING,
    COMPANY_SIZE        STRING,         -- SMB, Mid-Market, Enterprise
    REGION              STRING,
    COUNTRY             STRING,
    CREATED_DATE        DATE,
    TENANT_ID           STRING,         -- for multi-tenant demo (Week 4)
    INGESTED_AT         TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Support tickets
CREATE OR REPLACE TABLE SUPPORT_TICKETS (
    TICKET_ID           STRING      NOT NULL,
    CUSTOMER_ID         STRING      NOT NULL,
    CREATED_DATE        TIMESTAMP   NOT NULL,
    RESOLVED_DATE       TIMESTAMP,
    PRIORITY            STRING,         -- Low, Medium, High, Critical
    CATEGORY            STRING,
    DESCRIPTION         STRING,
    RESOLUTION          STRING,
    STATUS              STRING,         -- Open, In Progress, Resolved, Closed
    INGESTED_AT         TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- ============================================================
-- Load sample data
-- ============================================================

INSERT INTO CUSTOMERS VALUES
('C001', 'Acme Corp',       'Technology',     'Enterprise', 'North America', 'US', '2023-01-15', 'TENANT_A', CURRENT_TIMESTAMP()),
('C002', 'Beta Industries', 'Manufacturing',  'Mid-Market', 'EMEA',         'UK', '2023-03-20', 'TENANT_A', CURRENT_TIMESTAMP()),
('C003', 'Gamma Solutions', 'Finance',        'Enterprise', 'APAC',         'SG', '2023-06-10', 'TENANT_B', CURRENT_TIMESTAMP()),
('C004', 'Delta Services',  'Healthcare',     'SMB',        'North America', 'US', '2024-01-05', 'TENANT_B', CURRENT_TIMESTAMP()),
('C005', 'Epsilon Labs',    'Technology',     'Mid-Market', 'EMEA',         'DE', '2024-04-12', 'TENANT_A', CURRENT_TIMESTAMP());

INSERT INTO SALES_ORDERS VALUES
('ORD001', 'C001', '2025-01-15', 'Software',  'Platform License',  10, 5000.00, 5.00,  47500.00, 'North America', 'Alice', 'Won', CURRENT_TIMESTAMP()),
('ORD002', 'C002', '2025-02-20', 'Hardware',  'Server Rack',        2, 15000.00, 10.00, 27000.00, 'EMEA',          'Bob',   'Won', CURRENT_TIMESTAMP()),
('ORD003', 'C003', '2025-03-10', 'Services',  'Consulting',        40, 250.00,   0.00,  10000.00, 'APAC',          'Carol', 'Won', CURRENT_TIMESTAMP()),
('ORD004', 'C001', '2025-04-05', 'Software',  'Add-On Module',      5, 2000.00,  15.00,  8500.00, 'North America', 'Alice', 'Won', CURRENT_TIMESTAMP()),
('ORD005', 'C004', '2025-05-18', 'Hardware',  'Workstations',       8, 3000.00,  8.00,  22080.00, 'North America', 'Dave',  'Lost', CURRENT_TIMESTAMP()),
('ORD006', 'C005', '2025-06-22', 'Software',  'Platform License',   3, 5000.00,  12.00, 13200.00, 'EMEA',          'Bob',   'Open', CURRENT_TIMESTAMP());

INSERT INTO CUSTOMER_FEEDBACK VALUES
('FB001', 'C001', '2025-02-10 09:30:00', 'email',  'Great product, but onboarding was slow.',           3.5, 'Software',  'North America', CURRENT_TIMESTAMP()),
('FB002', 'C002', '2025-03-15 14:20:00', 'survey', 'Hardware arrived on time. Excellent quality.',       5.0, 'Hardware',  'EMEA',          CURRENT_TIMESTAMP()),
('FB003', 'C003', '2025-04-01 11:00:00', 'chat',   'Consulting engagement exceeded expectations.',      4.5, 'Services',  'APAC',          CURRENT_TIMESTAMP()),
('FB004', 'C004', '2025-05-20 16:45:00', 'call',   'Very disappointed. Delivery was 3 weeks late.',     1.5, 'Hardware',  'North America', CURRENT_TIMESTAMP()),
('FB005', 'C005', '2025-06-25 10:15:00', 'email',  'Module integration needs better documentation.',    3.0, 'Software',  'EMEA',          CURRENT_TIMESTAMP());

INSERT INTO SUPPORT_TICKETS VALUES
('TKT001', 'C001', '2025-02-12 08:00:00', '2025-02-14 17:00:00', 'Medium',   'Onboarding',     'User cannot complete setup wizard.',           'Walked through steps over call.',     'Resolved', CURRENT_TIMESTAMP()),
('TKT002', 'C004', '2025-05-21 09:30:00', NULL,                   'Critical', 'Delivery',        'Hardware order ORD005 not delivered on time.', NULL,                                   'Open',     CURRENT_TIMESTAMP()),
('TKT003', 'C005', '2025-06-26 11:00:00', '2025-06-28 10:00:00', 'Low',      'Documentation',   'Integration docs are outdated.',               'Updated docs link sent.',             'Closed',   CURRENT_TIMESTAMP());
