-- DocMind Setup SQL — App 2 of 10
-- Cortex Search + Multimodal AI + Stage → Enterprise Document Q&A

CREATE DATABASE IF NOT EXISTS DOCMIND;
CREATE SCHEMA  IF NOT EXISTS DOCMIND.PUBLIC;
USE DATABASE DOCMIND; USE SCHEMA PUBLIC;

-- Internal stage for documents (PDFs, DOCX, TXT, images)
CREATE OR REPLACE STAGE DOCMIND_STAGE
    DIRECTORY = (ENABLE = TRUE)
    ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE');

-- Document chunks table (source for Cortex Search)
CREATE OR REPLACE TABLE DOCUMENT_CHUNKS (
    CHUNK_ID       STRING DEFAULT 'CHK-' || UUID_STRING(),
    DOCUMENT_NAME  STRING NOT NULL,
    CHUNK_INDEX    INT,
    CHUNK_TEXT     STRING,
    SOURCE_TYPE    STRING,   -- 'pdf', 'docx', 'txt', 'image'
    CREATED_AT     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Cortex Search Service — managed RAG, no vector store to maintain
CREATE OR REPLACE CORTEX SEARCH SERVICE DOCMIND_SEARCH
    ON COLUMN CHUNK_TEXT
    ATTRIBUTES DOCUMENT_NAME, CHUNK_INDEX, SOURCE_TYPE
    WAREHOUSE = COMPUTE_WH
    TARGET_LAG = '1 hour'
    AS (
        SELECT CHUNK_TEXT, DOCUMENT_NAME, CHUNK_INDEX, SOURCE_TYPE, CREATED_AT
        FROM DOCUMENT_CHUNKS
    );

-- Q&A history for analytics
CREATE OR REPLACE TABLE QA_HISTORY (
    QA_ID          STRING DEFAULT UUID_STRING(),
    QUESTION       STRING,
    ANSWER         STRING,
    SOURCES_USED   VARIANT,
    ASKED_AT       TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    HELPFUL        BOOLEAN
);

-- Sample document chunks — representative of real ingested documents
INSERT INTO DOCUMENT_CHUNKS (DOCUMENT_NAME, CHUNK_INDEX, CHUNK_TEXT, SOURCE_TYPE) VALUES
('snowflake-cortex-overview.pdf', 1,
 'Snowflake Cortex is a suite of AI and ML capabilities fully managed inside Snowflake. It includes Cortex Analyst for natural language SQL, Cortex Search for semantic retrieval, AI_COMPLETE for LLM inference, and Arctic Embed for text vectorisation. No data leaves the Snowflake security perimeter.',
 'pdf'),
('snowflake-cortex-overview.pdf', 2,
 'Cortex Search is a managed RAG service. You define a CORTEX SEARCH SERVICE over any table column, set a TARGET_LAG, and Snowflake automatically keeps the search index in sync. Query it via the Python SDK or SQL. No vector store to provision or maintain.',
 'pdf'),
('data-governance-policy.docx', 1,
 'All tables containing customer PII must have a column-level masking policy applied before granting SELECT to non-privileged roles. PII columns include: EMAIL, PHONE, SSN, DATE_OF_BIRTH, HOME_ADDRESS. Review quarterly. Violations must be reported to the data governance board within 48 hours.',
 'docx'),
('data-governance-policy.docx', 2,
 'Row Access Policies must be applied to any table shared across business units. Each business unit may only see rows matching their TENANT_ID. Policies are defined in the GOVERNANCE schema and must be reviewed by the data platform team before activation.',
 'docx'),
('onboarding-runbook.txt', 1,
 'New data engineers are granted the DATA_ENGINEER role on day one. This role has CREATE TABLE in the LANDING and STAGING schemas only. Production schema write access requires a separate access request approved by the data platform lead. All requests logged in ServiceNow.',
 'txt'),
('onboarding-runbook.txt', 2,
 'To deploy a new Airflow DAG: 1) Create a feature branch from main. 2) Add the DAG file to dags/. 3) Add a pytest test in tests/dags/. 4) Open a PR. 5) CI must pass before merge. 6) Production deployment triggers automatically on merge to main via GitHub Actions.',
 'txt');

GRANT ALL ON DATABASE DOCMIND TO ROLE SYSADMIN;
GRANT ALL ON ALL TABLES  IN SCHEMA DOCMIND.PUBLIC TO ROLE SYSADMIN;
GRANT USAGE ON CORTEX SEARCH SERVICE DOCMIND.PUBLIC.DOCMIND_SEARCH TO ROLE SYSADMIN;
