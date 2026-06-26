-- SnowTrivia Setup SQL — App 10 of 10
CREATE DATABASE IF NOT EXISTS SNOW_TRIVIA; CREATE SCHEMA IF NOT EXISTS SNOW_TRIVIA.PUBLIC;
USE DATABASE SNOW_TRIVIA; USE SCHEMA PUBLIC;

CREATE STAGE IF NOT EXISTS KNOWLEDGE_STAGE;

CREATE OR REPLACE TABLE KNOWLEDGE_BASE (
    DOC_ID   STRING DEFAULT UUID_STRING() PRIMARY KEY,
    TOPIC    STRING, CONTENT STRING, SOURCE STRING,
    ADDED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Seed knowledge base with Snowflake topics
INSERT INTO KNOWLEDGE_BASE (TOPIC, CONTENT, SOURCE) VALUES
('Snowflake Architecture', 'Snowflake separates storage and compute. Storage uses cloud object storage (S3/Azure Blob/GCS). Compute uses virtual warehouses that can scale independently. This decoupling allows infinite scaling of storage without affecting compute costs, and vice versa.', 'Snowflake Docs'),
('Cortex AI', 'Snowflake Cortex is a suite of AI and ML capabilities built into Snowflake. It includes Cortex Analyst (NL to SQL), Cortex Search (semantic search), AI_COMPLETE (LLM inference), EMBED_TEXT_768 (Arctic Embed vectors), and Snowpark ML (model training). All capabilities run inside Snowflake without data egress.', 'Snowflake Cortex Docs'),
('Zero-Copy Clone', 'Zero-copy cloning creates a clone of a table, schema, or database without copying data. It uses metadata pointers. Storage is only consumed when cloned data diverges from the source. Common uses: dev/test environments, point-in-time snapshots, A/B testing new transformations.', 'Snowflake Features'),
('Data Sharing', 'Snowflake Secure Data Sharing allows sharing live data across accounts without copying it. The data provider creates a share, grants access to objects, and consumers query the shared data as if it were local. No data movement. No ETL. Updates are immediately visible to consumers.', 'Snowflake Docs'),
('Time Travel', 'Snowflake Time Travel allows accessing historical data at any point within the configured retention period (1-90 days for Enterprise). Use AT or BEFORE clause: SELECT * FROM table AT (TIMESTAMP => ...). Useful for auditing, recovering accidentally deleted data, and reproducing historical reports.', 'Snowflake Time Travel');

CREATE OR REPLACE CORTEX SEARCH SERVICE KNOWLEDGE_SEARCH
    ON COLUMN CONTENT ATTRIBUTES TOPIC, SOURCE
    WAREHOUSE = COMPUTE_WH TARGET_LAG = '1 hour'
    AS (SELECT CONTENT, TOPIC, SOURCE, DOC_ID FROM KNOWLEDGE_BASE);

CREATE OR REPLACE TABLE GAME_SESSIONS (
    SESSION_ID  STRING DEFAULT UUID_STRING() PRIMARY KEY,
    PLAYER_NAME STRING, TOPIC STRING,
    SCORE INT DEFAULT 0, TOTAL_QUESTIONS INT DEFAULT 0,
    MAX_STREAK  INT DEFAULT 0, DIFFICULTY STRING DEFAULT 'beginner',
    STARTED_AT  TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    ENDED_AT    TIMESTAMP_NTZ
);

CREATE OR REPLACE TABLE LEADERBOARD (
    PLAYER_NAME STRING, TOPIC STRING,
    BEST_SCORE  INT, BEST_PCT FLOAT, GAMES_PLAYED INT,
    LAST_PLAYED TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);
