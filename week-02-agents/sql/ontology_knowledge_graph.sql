-- ============================================================
-- Day 7 UPDATE: Ontology-Grounded Agent Reasoning
-- ============================================================
-- Reference: https://www.snowflake.com/en/blog/engineering/ontology-grounded-cortex-agents/
-- Knowledge Graph + GraphRAG on top of Semantic Views
-- Benchmark: 50% → 78% accuracy with ontology grounding

-- ============================================================
-- Step 1: Build a Knowledge Graph in Snowflake (node-edge model)
-- ============================================================
CREATE OR REPLACE TABLE REVENUE_OPS_AI.ANALYTICS.KG_NODE (
    NODE_ID STRING PRIMARY KEY,
    NODE_TYPE STRING,       -- 'product', 'region', 'customer_segment', 'metric'
    NODE_NAME STRING,
    SYNONYMS ARRAY,         -- alternative names
    PROPERTIES VARIANT      -- flexible metadata
);

CREATE OR REPLACE TABLE REVENUE_OPS_AI.ANALYTICS.KG_EDGE (
    SRC_NODE_ID STRING,
    DST_NODE_ID STRING,
    EDGE_TYPE STRING,       -- 'belongs_to', 'drives', 'impacts', 'subclass_of'
    WEIGHT FLOAT DEFAULT 1.0,
    METADATA VARIANT,
    FOREIGN KEY (SRC_NODE_ID) REFERENCES KG_NODE(NODE_ID),
    FOREIGN KEY (DST_NODE_ID) REFERENCES KG_NODE(NODE_ID)
);

-- Seed Revenue Ops ontology
INSERT INTO REVENUE_OPS_AI.ANALYTICS.KG_NODE VALUES
    ('PROD_ENT', 'product', 'Enterprise Suite', ['Enterprise', 'Ent Suite'], NULL),
    ('PROD_PRO', 'product', 'Professional', ['Pro', 'Professional Plan'], NULL),
    ('REG_NA', 'region', 'North America', ['NA', 'US', 'United States', 'Canada'], NULL),
    ('REG_EMEA', 'region', 'EMEA', ['Europe', 'EU', 'Middle East', 'Africa'], NULL),
    ('SEG_ENT', 'segment', 'Enterprise Segment', ['Large Enterprise', 'Fortune 500'], NULL),
    ('SEG_MM', 'segment', 'Mid-Market Segment', ['Mid-Market', 'Growth'], NULL),
    ('MET_ARR', 'metric', 'Annual Recurring Revenue', ['ARR', 'recurring revenue'], NULL),
    ('MET_CHURN', 'metric', 'Churn Rate', ['churn', 'attrition', 'customer loss'], NULL);

INSERT INTO REVENUE_OPS_AI.ANALYTICS.KG_EDGE VALUES
    ('PROD_ENT', 'SEG_ENT', 'targets', 1.0, NULL),
    ('PROD_PRO', 'SEG_MM', 'targets', 1.0, NULL),
    ('SEG_ENT', 'REG_NA', 'concentrated_in', 0.7, NULL),
    ('MET_ARR', 'PROD_ENT', 'driven_by', 0.6, NULL),
    ('MET_CHURN', 'SEG_MM', 'impacts', 0.8, NULL);

-- ============================================================
-- Step 2: Recursive CTE for Knowledge Graph Traversal
-- ============================================================
-- Find all entities connected to "Annual Recurring Revenue" within 3 hops
WITH RECURSIVE paths AS (
    -- Anchor: start from ARR metric
    SELECT
        e.SRC_NODE_ID AS root,
        e.DST_NODE_ID AS leaf,
        ARRAY_CONSTRUCT(e.SRC_NODE_ID, e.DST_NODE_ID) AS path,
        e.EDGE_TYPE AS relationship_chain,
        1 AS depth
    FROM REVENUE_OPS_AI.ANALYTICS.KG_EDGE e
    WHERE e.SRC_NODE_ID = 'MET_ARR'

    UNION ALL

    -- Recursive: extend by one hop
    SELECT
        p.root,
        e.DST_NODE_ID,
        ARRAY_APPEND(p.path, e.DST_NODE_ID),
        p.relationship_chain || ' → ' || e.EDGE_TYPE,
        p.depth + 1
    FROM paths p
    JOIN REVENUE_OPS_AI.ANALYTICS.KG_EDGE e
        ON p.leaf = e.SRC_NODE_ID
    WHERE NOT ARRAY_CONTAINS(e.DST_NODE_ID::VARIANT, p.path) -- avoid cycles
      AND p.depth < 3
)
SELECT
    p.root,
    n.NODE_NAME AS connected_entity,
    n.NODE_TYPE AS entity_type,
    p.relationship_chain,
    p.depth
FROM paths p
JOIN REVENUE_OPS_AI.ANALYTICS.KG_NODE n ON p.leaf = n.NODE_ID
ORDER BY p.depth, n.NODE_TYPE;

-- ============================================================
-- Step 3: GraphRAG Index for Cortex Search
-- ============================================================
-- Flatten knowledge graph into searchable profiles
CREATE OR REPLACE TABLE REVENUE_OPS_AI.ANALYTICS.GRAPHRAG_INDEX AS
WITH node_profiles AS (
    SELECT
        n.NODE_ID,
        n.NODE_TYPE,
        n.NODE_NAME,
        ARRAY_TO_STRING(n.SYNONYMS, ', ') AS synonyms,
        LISTAGG(DISTINCT e_out.EDGE_TYPE || ' → ' || n2.NODE_NAME, '; ')
            WITHIN GROUP (ORDER BY n2.NODE_NAME) AS outgoing_relations,
        LISTAGG(DISTINCT n3.NODE_NAME || ' ' || e_in.EDGE_TYPE, '; ')
            WITHIN GROUP (ORDER BY n3.NODE_NAME) AS incoming_relations
    FROM REVENUE_OPS_AI.ANALYTICS.KG_NODE n
    LEFT JOIN REVENUE_OPS_AI.ANALYTICS.KG_EDGE e_out ON n.NODE_ID = e_out.SRC_NODE_ID
    LEFT JOIN REVENUE_OPS_AI.ANALYTICS.KG_NODE n2 ON e_out.DST_NODE_ID = n2.NODE_ID
    LEFT JOIN REVENUE_OPS_AI.ANALYTICS.KG_EDGE e_in ON n.NODE_ID = e_in.DST_NODE_ID
    LEFT JOIN REVENUE_OPS_AI.ANALYTICS.KG_NODE n3 ON e_in.SRC_NODE_ID = n3.NODE_ID
    GROUP BY n.NODE_ID, n.NODE_TYPE, n.NODE_NAME, n.SYNONYMS
)
SELECT
    NODE_ID,
    NODE_TYPE,
    NODE_NAME,
    NODE_NAME || '. Also known as: ' || COALESCE(synonyms, 'N/A')
        || '. Outgoing: ' || COALESCE(outgoing_relations, 'none')
        || '. Incoming: ' || COALESCE(incoming_relations, 'none')
    AS PROFILE_TEXT
FROM node_profiles;

-- Create Cortex Search service on the flattened profiles
-- CREATE OR REPLACE CORTEX SEARCH SERVICE REVENUE_OPS_AI.ANALYTICS.KG_SEARCH
--     ON PROFILE_TEXT
--     WAREHOUSE = COMPUTE_WH
--     TARGET_LAG = '1 hour'
--     AS SELECT * FROM REVENUE_OPS_AI.ANALYTICS.GRAPHRAG_INDEX;
