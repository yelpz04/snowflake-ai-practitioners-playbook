"""
============================================================
Article 2: Audio + Video Intelligence
Days 3–4 of The Snowflake AI Practitioner's Playbook
============================================================
Series: https://github.com/yelpz04/snowflake-ai-practitioners-playbook
Folder: week-01-multimodal/python/

What this file covers (Article 2):
  - Analyse customer support call recordings for sentiment + churn signals
  - Extract compliance violations from video content
  - Batch-process audio/video files from a Snowflake stage
  - Store AI output to AI_OUTPUTS.MEDIA_AI_RESULTS for downstream use

Prerequisites:
  - MEDIA_FILES_STAGE created (week-01-multimodal/sql/02_create_media_stage.sql)
  - MEDIA_AI_RESULTS table created (week-01-multimodal/sql/01_create_feedback_tables.sql)
  - Audio/video files uploaded with AUTO_COMPRESS=FALSE
  - pip install snowflake-connector-python

NOTE: Audio and video multimodal AI is Public Preview as of Summit 2026.
      Check region availability before using in production.
      Docs: https://docs.snowflake.com/en/user-guide/snowflake-cortex/ai-multimodal
============================================================
"""

import snowflake.connector
import json

# ============================================================
# Connection
# ============================================================

conn = snowflake.connector.connect(
    account="YOUR_ACCOUNT",
    user="YOUR_USER",
    authenticator="externalbrowser",
    database="REVENUE_OPS_AI",
    schema="RAW",
    warehouse="REVOPS_AI_WH"
)
cur = conn.cursor()


# ============================================================
# Audio Analysis — Call Recording Intelligence (Day 3)
# Extracts: sentiment, churn signals, escalation risk,
# recommended follow-up actions
# ============================================================

def analyse_call_recording(stage_path: str, customer_id: str) -> dict:
    """
    Analyse a call recording for sentiment and churn risk.
    Returns structured JSON inserted into MEDIA_AI_RESULTS.
    """
    cur.execute(f"""
        SELECT SNOWFLAKE.CORTEX.AI_COMPLETE(
            'claude-3-5-sonnet',
            'Analyse this customer support call recording. Return JSON with:
             sentiment (positive/neutral/negative),
             sentiment_score (float -1.0 to 1.0),
             churn_risk (low/medium/high),
             churn_risk_score (float 0.0 to 1.0),
             escalation_signals (array of strings — specific phrases or moments),
             key_topics (array of strings),
             recommended_action (string — what the account team should do next),
             call_summary (2-3 sentence summary),
             confidence_score (float 0.0 to 1.0).',
            {{'media': [{{'type': 'audio', 'source': {{'type': 'stage',
              'stage': '@REVENUE_OPS_AI.RAW.MEDIA_FILES_STAGE',
              'path': '{stage_path}'}}}}]}}
        )
    """)
    result = cur.fetchone()[0]
    ai_output = json.loads(result) if isinstance(result, str) else result

    cur.execute("""
        INSERT INTO AI_OUTPUTS.MEDIA_AI_RESULTS
            (RESULT_ID, FILE_ID, FILE_TYPE, AI_MODEL,
             PROCESSING_TYPE, AI_OUTPUT, SUMMARY, PROCESSED_AT)
        VALUES (
            'RES-AUD-' || UUID_STRING(), %s, 'audio',
            'claude-3-5-sonnet', 'call_intelligence',
            TRY_PARSE_JSON(%s), %s, CURRENT_TIMESTAMP()
        )
    """, (customer_id, json.dumps(ai_output), ai_output.get("call_summary", "")))

    cur.execute("""
        INSERT INTO AI_OUTPUTS.CALL_AI_INSIGHTS
            (INSIGHT_ID, CUSTOMER_ID, CALL_DATE, SENTIMENT,
             SENTIMENT_SCORE, CHURN_RISK, CHURN_RISK_SCORE,
             ESCALATION_SIGNALS, KEY_TOPICS, RECOMMENDED_ACTION, ANALYZED_AT)
        VALUES (
            'INS-' || UUID_STRING(), %s, CURRENT_DATE(),
            %s, %s, %s, %s,
            ARRAY_CONSTRUCT(%s), ARRAY_CONSTRUCT(%s),
            %s, CURRENT_TIMESTAMP()
        )
    """, (
        customer_id,
        ai_output.get("sentiment", "neutral"),
        float(ai_output.get("sentiment_score", 0.0)),
        ai_output.get("churn_risk", "low"),
        float(ai_output.get("churn_risk_score", 0.0)),
        json.dumps(ai_output.get("escalation_signals", [])),
        json.dumps(ai_output.get("key_topics", [])),
        ai_output.get("recommended_action", "")
    ))
    conn.commit()
    return ai_output


# ============================================================
# Video Analysis — Compliance + Brand Monitoring (Day 4)
# Extracts: brand violations, policy breaches, content tags
# ============================================================

def analyse_video_compliance(stage_path: str, file_id: str) -> dict:
    """
    Scan a video for brand guideline violations and content compliance.
    Returns structured JSON inserted into MEDIA_AI_RESULTS.
    """
    cur.execute(f"""
        SELECT SNOWFLAKE.CORTEX.AI_COMPLETE(
            'claude-3-5-sonnet',
            'Analyse this video for compliance and brand safety. Return JSON with:
             overall_compliance (pass/warn/fail),
             brand_violations (array — specific timestamps and descriptions),
             policy_breaches (array — any regulatory or policy issues found),
             content_tags (array — descriptive tags for cataloging),
             recommended_action (string — approve/edit/reject with reason),
             confidence_score (float 0.0 to 1.0).',
            {{'media': [{{'type': 'video', 'source': {{'type': 'stage',
              'stage': '@REVENUE_OPS_AI.RAW.MEDIA_FILES_STAGE',
              'path': '{stage_path}'}}}}]}}
        )
    """)
    result = cur.fetchone()[0]
    ai_output = json.loads(result) if isinstance(result, str) else result

    cur.execute("""
        INSERT INTO AI_OUTPUTS.MEDIA_AI_RESULTS
            (RESULT_ID, FILE_ID, FILE_TYPE, AI_MODEL,
             PROCESSING_TYPE, AI_OUTPUT, SUMMARY, PROCESSED_AT)
        VALUES (
            'RES-VID-' || UUID_STRING(), %s, 'video',
            'claude-3-5-sonnet', 'compliance_check',
            TRY_PARSE_JSON(%s), %s, CURRENT_TIMESTAMP()
        )
    """, (
        file_id,
        json.dumps(ai_output),
        f"Compliance: {ai_output.get('overall_compliance', 'unknown')} — "
        f"{ai_output.get('recommended_action', '')}"
    ))
    conn.commit()
    return ai_output


# ============================================================
# Batch processor — runs against all unprocessed media files
# ============================================================

def run_batch():
    cur.execute("""
        SELECT FILE_ID, FILE_PATH, FILE_TYPE, CONTEXT
        FROM MEDIA_FILES
        WHERE FILE_TYPE IN ('audio', 'video')
          AND AI_PROCESSED = FALSE
        ORDER BY FILE_TYPE, INGESTED_AT
    """)
    files = cur.fetchall()
    print(f"Found {len(files)} unprocessed audio/video files")

    for file_id, file_path, file_type, context in files:
        try:
            stage_path = file_path.split("@MEDIA_FILES_STAGE/")[1]

            if file_type == "audio":
                result = analyse_call_recording(stage_path, customer_id=file_id)
                print(f"  ✓ {file_id} | sentiment={result.get('sentiment')} "
                      f"churn_risk={result.get('churn_risk')}")
            elif file_type == "video":
                result = analyse_video_compliance(stage_path, file_id=file_id)
                print(f"  ✓ {file_id} | compliance={result.get('overall_compliance')}")

            cur.execute("""
                UPDATE MEDIA_FILES
                SET AI_PROCESSED = TRUE, AI_PROCESSED_AT = CURRENT_TIMESTAMP()
                WHERE FILE_ID = %s
            """, (file_id,))
            conn.commit()

        except Exception as e:
            print(f"  ✗ {file_id} failed: {e}")
            conn.rollback()

    cur.close()
    conn.close()


if __name__ == "__main__":
    run_batch()
