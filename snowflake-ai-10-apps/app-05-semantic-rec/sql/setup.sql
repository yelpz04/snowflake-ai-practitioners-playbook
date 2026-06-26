-- SemanticRec Setup SQL — App 5 of 10
CREATE DATABASE IF NOT EXISTS SEMANTICREC; CREATE SCHEMA IF NOT EXISTS SEMANTICREC.PUBLIC;
USE DATABASE SEMANTICREC; USE SCHEMA PUBLIC;

CREATE OR REPLACE TABLE CONTENT (
    CONTENT_ID       STRING DEFAULT UUID_STRING() PRIMARY KEY,
    TITLE            STRING NOT NULL, BODY STRING,
    CATEGORY         STRING, TAGS ARRAY, AUTHOR STRING,
    VIEW_COUNT       INT DEFAULT 0, VIEW_COUNT_7D INT DEFAULT 0,
    POSITIVE_REACTIONS INT DEFAULT 0, NEGATIVE_REACTIONS INT DEFAULT 0,
    CONTENT_VECTOR   VECTOR(FLOAT, 768),
    CREATED_AT       TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE OR REPLACE TABLE USER_HISTORY (
    USER_ID STRING, CONTENT_ID STRING, VIEWED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Seed sample content
INSERT INTO CONTENT (TITLE, BODY, CATEGORY, AUTHOR, VIEW_COUNT)
VALUES
('Getting Started with Snowflake Cortex AI', 'Snowflake Cortex is a suite of AI and ML capabilities...', 'AI', 'admin', 1500),
('Vector Search Explained Simply', 'Vector search works by converting text to numerical representations...', 'ML', 'admin', 1200),
('Building RAG Applications in Production', 'Retrieval-Augmented Generation combines LLMs with your own data...', 'AI', 'admin', 980),
('Data Quality at Scale with DMF', 'Data Metric Functions are Snowflake-native quality checks...', 'Data Engineering', 'admin', 750),
('Zero-Copy Cloning for Dev/Test Environments', 'Snowflake zero-copy clone creates a pointer to existing data...', 'Snowflake', 'admin', 660);

-- Populate vectors (run manually or via task)
UPDATE CONTENT
SET CONTENT_VECTOR = SNOWFLAKE.CORTEX.EMBED_TEXT_768('snowflake-arctic-embed-m', TITLE || ' ' || LEFT(BODY, 500))
WHERE CONTENT_VECTOR IS NULL;

CREATE OR REPLACE CORTEX SEARCH SERVICE CONTENT_SEARCH
    ON COLUMN BODY ATTRIBUTES TITLE, CATEGORY, AUTHOR
    WAREHOUSE = COMPUTE_WH TARGET_LAG = '1 hour'
    AS (SELECT BODY, TITLE, CATEGORY, AUTHOR, CONTENT_ID FROM CONTENT);

-- Task: refresh embeddings nightly
CREATE OR REPLACE TASK REFRESH_EMBEDDINGS
    WAREHOUSE = COMPUTE_WH SCHEDULE = 'USING CRON 0 2 * * * UTC'
AS
UPDATE CONTENT
SET CONTENT_VECTOR = SNOWFLAKE.CORTEX.EMBED_TEXT_768('snowflake-arctic-embed-m', TITLE || ' ' || LEFT(BODY, 500))
WHERE CONTENT_VECTOR IS NULL OR CREATED_AT > DATEADD(hour, -25, CURRENT_TIMESTAMP());
ALTER TASK REFRESH_EMBEDDINGS RESUME;
