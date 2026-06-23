-- ============================================================
-- Create stages for media files (images, audio, video)
-- ============================================================

USE SCHEMA REVENUE_OPS_AI.RAW;

-- Internal stage for all media files
CREATE OR REPLACE STAGE MEDIA_FILES_STAGE
    DIRECTORY = (ENABLE = TRUE)
    ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE');

-- Table to track uploaded media files and their AI processing status
CREATE OR REPLACE TABLE MEDIA_FILES (
    FILE_ID             STRING          NOT NULL,
    FILE_NAME           STRING          NOT NULL,
    FILE_TYPE           STRING,             -- image, audio, video, document
    FILE_PATH           STRING,             -- stage path: @MEDIA_FILES_STAGE/...
    UPLOADED_BY         STRING,
    UPLOADED_AT         TIMESTAMP_NTZ   DEFAULT CURRENT_TIMESTAMP(),
    FILE_SIZE_BYTES     NUMBER,
    CONTENT_TYPE        STRING,             -- image/png, audio/wav, video/mp4, etc.
    CONTEXT             STRING,             -- what is this file about (customer call, product image, etc.)
    CUSTOMER_ID         STRING,
    AI_PROCESSED        BOOLEAN         DEFAULT FALSE,
    AI_PROCESSED_AT     TIMESTAMP_NTZ
);

-- Table for AI results from multimodal processing
CREATE OR REPLACE TABLE REVENUE_OPS_AI.AI_OUTPUTS.MEDIA_AI_RESULTS (
    RESULT_ID           STRING          NOT NULL,
    FILE_ID             STRING          NOT NULL,
    FILE_TYPE           STRING,
    AI_MODEL            STRING,             -- e.g., 'claude-3-5-sonnet'
    PROCESSING_TYPE     STRING,             -- extraction, sentiment, summary, metadata
    AI_OUTPUT           VARIANT,            -- full JSON output from AI_COMPLETE
    EXTRACTED_TEXT      STRING,
    SENTIMENT           STRING,
    SENTIMENT_SCORE     FLOAT,
    SUMMARY             STRING,
    TAGS                ARRAY,
    PROCESSED_AT        TIMESTAMP_NTZ   DEFAULT CURRENT_TIMESTAMP()
);

-- ============================================================
-- Upload instructions (run from SnowSQL or Snowsight)
-- ============================================================

-- Upload sample files to the stage:
-- PUT file:///path/to/invoice.png @MEDIA_FILES_STAGE/images/ AUTO_COMPRESS=FALSE;
-- PUT file:///path/to/call_recording.wav @MEDIA_FILES_STAGE/audio/ AUTO_COMPRESS=FALSE;
-- PUT file:///path/to/demo_video.mp4 @MEDIA_FILES_STAGE/video/ AUTO_COMPRESS=FALSE;

-- Verify uploads:
-- LIST @MEDIA_FILES_STAGE;

-- Register files in tracking table:
INSERT INTO MEDIA_FILES (FILE_ID, FILE_NAME, FILE_TYPE, FILE_PATH, UPLOADED_BY, FILE_SIZE_BYTES, CONTENT_TYPE, CONTEXT, CUSTOMER_ID)
VALUES
    ('MF001', 'invoice_acme_jan2025.png',   'image', '@MEDIA_FILES_STAGE/images/invoice_acme_jan2025.png',   'admin', 245000,  'image/png',  'Invoice scan from Acme Corp',          'C001'),
    ('MF002', 'product_photo_server.jpg',   'image', '@MEDIA_FILES_STAGE/images/product_photo_server.jpg',   'admin', 180000,  'image/jpeg', 'Product photo for catalog',             NULL),
    ('MF003', 'support_call_delta.wav',     'audio', '@MEDIA_FILES_STAGE/audio/support_call_delta.wav',      'admin', 5200000, 'audio/wav',  'Support escalation call from Delta',    'C004'),
    ('MF004', 'product_demo_q1.mp4',        'video', '@MEDIA_FILES_STAGE/video/product_demo_q1.mp4',        'admin', 42000000,'video/mp4',  'Q1 product demo for marketing review',  NULL);
