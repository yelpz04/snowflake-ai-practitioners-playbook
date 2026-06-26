-- MediaIntel Setup SQL — App 6 of 10
CREATE DATABASE IF NOT EXISTS MEDIA_INTEL; CREATE SCHEMA IF NOT EXISTS MEDIA_INTEL.PUBLIC;
USE DATABASE MEDIA_INTEL; USE SCHEMA PUBLIC;

CREATE STAGE IF NOT EXISTS MEDIA_STAGE ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE');

CREATE OR REPLACE TABLE MEDIA_ASSETS (
    ASSET_ID     STRING DEFAULT UUID_STRING() PRIMARY KEY,
    MEDIA_FILE_NAME STRING NOT NULL, ASSET_TYPE STRING,   -- IMAGE / AUDIO / VIDEO
    FILE_SIZE_KB INT, UPLOADED_BY STRING, UPLOADED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE OR REPLACE TABLE MEDIA_CATALOG (
    ASSET_ID       STRING, MEDIA_FILE_NAME STRING, ASSET_TYPE STRING,
    AI_OUTPUT      VARIANT,
    -- parsed convenience columns
    SUMMARY        STRING    AS (AI_OUTPUT:summary::STRING),
    SENTIMENT      STRING    AS (AI_OUTPUT:sentiment::STRING),
    COMPLIANCE_FLAGS ARRAY   AS (AI_OUTPUT:compliance_flags::ARRAY),
    TOPICS         ARRAY     AS (AI_OUTPUT:topics::ARRAY),
    TAGS           ARRAY     AS (AI_OUTPUT:tags::ARRAY),
    TRANSCRIPT     STRING    AS (AI_OUTPUT:transcript::STRING),
    ANALYSED_AT    TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE OR REPLACE CORTEX SEARCH SERVICE MEDIA_SEARCH
    ON COLUMN TRANSCRIPT
    ATTRIBUTES MEDIA_FILE_NAME, ASSET_TYPE, SENTIMENT
    WAREHOUSE = COMPUTE_WH TARGET_LAG = '1 hour'
    AS (SELECT TRANSCRIPT, SUMMARY, MEDIA_FILE_NAME, ASSET_TYPE, SENTIMENT FROM MEDIA_CATALOG);

-- ── Sample data (pre-analysed assets for demo without uploading real files) ──
INSERT INTO MEDIA_ASSETS (MEDIA_FILE_NAME, ASSET_TYPE, FILE_SIZE_KB, UPLOADED_BY) VALUES
('product-launch-hero.jpg',   'IMAGE', 840,  'marketing@acme.com'),
('q3-earnings-podcast.mp3',   'AUDIO', 22400,'finance@acme.com'),
('brand-tv-spot-30s.mp4',     'VIDEO', 48200,'brand@acme.com'),
('compliance-banner-ad.jpg',  'IMAGE', 320,  'legal@acme.com'),
('customer-testimonial.mp4',  'VIDEO', 18900,'cx@acme.com');

INSERT INTO MEDIA_CATALOG (MEDIA_FILE_NAME, ASSET_TYPE, AI_OUTPUT) VALUES
('product-launch-hero.jpg', 'IMAGE',
 PARSE_JSON('{"category":"Product Photography","detected_text":["New in 2026","Pre-order Now"],"dominant_colors":["#0A2540","#FFFFFF","#635BFF"],"brand_present":true,"quality_score":9,"tags":["product","launch","premium","clean"],"summary":"High-quality hero image for a product launch. Features the product centred on a dark background with white text overlay and brand colours.","sentiment":"positive","compliance_flags":[]}')),
('q3-earnings-podcast.mp3', 'AUDIO',
 PARSE_JSON('{"transcript":"Welcome to the Q3 earnings call. Revenue grew 18% year over year to 4.2 billion dollars. Operating margin expanded by 200 basis points. We are raising full-year guidance by 5 percent.","summary":"Q3 earnings call recording. Revenue up 18% YoY to $4.2B, operating margin improved, full-year guidance raised.","topics":["revenue","earnings","guidance","margin"],"sentiment":"positive","speaker_count":2,"language":"en","compliance_flags":[]}')),
('brand-tv-spot-30s.mp4', 'VIDEO',
 PARSE_JSON('{"scene_count":6,"topics":["brand awareness","product features","call to action"],"mood":"energetic","text_on_screen":["Fast.","Smart.","Yours.","Visit acme.com"],"compliance_flags":[],"summary":"30-second brand TV spot. Opens with product close-up, transitions through lifestyle scenes, closes with logo and URL. Upbeat music throughout.","transcript":null}')),
('compliance-banner-ad.jpg', 'IMAGE',
 PARSE_JSON('{"category":"Digital Advertising","detected_text":["50% OFF","Today Only","Terms Apply"],"dominant_colors":["#FF0000","#FFFFFF"],"brand_present":true,"quality_score":6,"tags":["promotion","discount","banner","ad"],"summary":"Promotional banner ad with discount offer. Red background with bold white text. Standard digital ad format.","sentiment":"neutral","compliance_flags":["unsubstantiated_claim: 50% OFF requires asterisk and terms disclosure"]}')),
('customer-testimonial.mp4', 'VIDEO',
 PARSE_JSON('{"scene_count":3,"topics":["customer success","product satisfaction","ROI"],"mood":"authentic","text_on_screen":["Sarah M., VP Engineering"],"compliance_flags":[],"summary":"Customer testimonial video featuring VP Engineering discussing 40% reduction in pipeline failures after adopting the platform. Authentic, unscripted feel.","transcript":"Since we started using this platform, our pipeline failure rate dropped by 40 percent. The team spends less time firefighting and more time building new features."}'));
