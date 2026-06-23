-- ============================================================
-- Days 2–4: Cortex AI Multimodal Queries
-- ============================================================
-- IMPORTANT: Multimodal AI with audio/video is Public Preview.
-- Requires: AI_COMPLETE function access + files on a Snowflake stage.
-- Docs: https://docs.snowflake.com/en/user-guide/snowflake-cortex/ai-multimodal
-- ============================================================

USE SCHEMA REVENUE_OPS_AI.AI_OUTPUTS;

-- ============================================================
-- Document / Image Extraction
-- ============================================================

-- Extract structured data from an invoice image
SELECT
    SNOWFLAKE.CORTEX.AI_COMPLETE(
        'claude-3-5-sonnet',
        'Extract the following fields from this invoice image as JSON: 
         invoice_number, date, vendor_name, line_items (array of {description, quantity, unit_price, total}), 
         subtotal, tax, total_due, due_date.',
        {
            'media': [
                {
                    'type': 'image',
                    'source': {
                        'type': 'stage',
                        'stage': '@REVENUE_OPS_AI.RAW.MEDIA_FILES_STAGE',
                        'path': 'images/invoice_acme_jan2025.png'
                    }
                }
            ]
        }
    ) AS invoice_extraction;

-- Extract product details from a product photo
SELECT
    SNOWFLAKE.CORTEX.AI_COMPLETE(
        'claude-3-5-sonnet',
        'Analyze this product photo. Return JSON with: 
         product_type, brand_visible (bool), condition, 
         color, notable_features, suggested_catalog_tags (array).',
        {
            'media': [
                {
                    'type': 'image',
                    'source': {
                        'type': 'stage',
                        'stage': '@REVENUE_OPS_AI.RAW.MEDIA_FILES_STAGE',
                        'path': 'images/product_photo_server.jpg'
                    }
                }
            ]
        }
    ) AS product_analysis;

-- Insert image results into AI results table
INSERT INTO MEDIA_AI_RESULTS (RESULT_ID, FILE_ID, FILE_TYPE, AI_MODEL, PROCESSING_TYPE, AI_OUTPUT, SUMMARY, PROCESSED_AT)
SELECT
    'RES-IMG-' || UUID_STRING(),
    'MF001',
    'image',
    'claude-3-5-sonnet',
    'extraction',
    PARSE_JSON(
        SNOWFLAKE.CORTEX.AI_COMPLETE(
            'claude-3-5-sonnet',
            'Extract invoice fields as JSON: invoice_number, date, vendor_name, line_items, subtotal, tax, total_due.',
            {
                'media': [{ 'type': 'image', 'source': { 'type': 'stage', 'stage': '@REVENUE_OPS_AI.RAW.MEDIA_FILES_STAGE', 'path': 'images/invoice_acme_jan2025.png' } }]
            }
        )
    ),
    'Invoice data extracted from scanned image',
    CURRENT_TIMESTAMP();


-- ============================================================
-- Audio Sentiment Analysis
-- ============================================================

-- Analyze a customer support call recording for sentiment + escalation signals
SELECT
    SNOWFLAKE.CORTEX.AI_COMPLETE(
        'claude-3-5-sonnet',
        'Analyze this customer support call recording. Return JSON with:
         - overall_sentiment (positive/negative/neutral/mixed)
         - sentiment_score (-1.0 to 1.0)
         - customer_emotion (calm/frustrated/angry/satisfied)
         - escalation_detected (bool)
         - escalation_reason (string, null if none)
         - key_issues (array of strings)
         - resolution_offered (bool)
         - call_summary (2-3 sentences)
         - recommended_follow_up (string)',
        {
            'media': [
                {
                    'type': 'audio',
                    'source': {
                        'type': 'stage',
                        'stage': '@REVENUE_OPS_AI.RAW.MEDIA_FILES_STAGE',
                        'path': 'audio/support_call_delta.wav'
                    }
                }
            ]
        }
    ) AS call_sentiment_analysis;

-- Store audio analysis into dedicated table
CREATE OR REPLACE TABLE REVENUE_OPS_AI.AI_OUTPUTS.CALL_AI_INSIGHTS (
    INSIGHT_ID          STRING          NOT NULL,
    FILE_ID             STRING          NOT NULL,
    CUSTOMER_ID         STRING,
    CALL_DATE           TIMESTAMP,
    OVERALL_SENTIMENT   STRING,
    SENTIMENT_SCORE     FLOAT,
    CUSTOMER_EMOTION    STRING,
    ESCALATION_DETECTED BOOLEAN,
    ESCALATION_REASON   STRING,
    KEY_ISSUES          ARRAY,
    RESOLUTION_OFFERED  BOOLEAN,
    CALL_SUMMARY        STRING,
    RECOMMENDED_FOLLOWUP STRING,
    RAW_AI_OUTPUT       VARIANT,
    PROCESSED_AT        TIMESTAMP_NTZ   DEFAULT CURRENT_TIMESTAMP()
);


-- ============================================================
-- Video Metadata Extraction
-- ============================================================

-- Analyze a product demo video for content intelligence
SELECT
    SNOWFLAKE.CORTEX.AI_COMPLETE(
        'claude-3-5-sonnet',
        'Analyze this product demo video. Return JSON with:
         - video_summary (3-5 sentences)
         - duration_estimate (string)
         - visible_products (array of strings)
         - brand_mentions (array of strings)
         - content_themes (array of strings)
         - speaker_count (number)
         - overall_tone (professional/casual/energetic/informative)
         - content_safety (safe/review_needed with reason)
         - marketing_quality_score (1-10)
         - suggested_audience (string)',
        {
            'media': [
                {
                    'type': 'video',
                    'source': {
                        'type': 'stage',
                        'stage': '@REVENUE_OPS_AI.RAW.MEDIA_FILES_STAGE',
                        'path': 'video/product_demo_q1.mp4'
                    }
                }
            ]
        }
    ) AS video_analysis;

-- Store video analysis
CREATE OR REPLACE TABLE REVENUE_OPS_AI.AI_OUTPUTS.VIDEO_AI_INSIGHTS (
    INSIGHT_ID              STRING      NOT NULL,
    FILE_ID                 STRING      NOT NULL,
    VIDEO_SUMMARY           STRING,
    VISIBLE_PRODUCTS        ARRAY,
    BRAND_MENTIONS          ARRAY,
    CONTENT_THEMES          ARRAY,
    SPEAKER_COUNT           NUMBER,
    OVERALL_TONE            STRING,
    CONTENT_SAFETY          STRING,
    MARKETING_QUALITY_SCORE NUMBER,
    SUGGESTED_AUDIENCE      STRING,
    RAW_AI_OUTPUT           VARIANT,
    PROCESSED_AT            TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);
