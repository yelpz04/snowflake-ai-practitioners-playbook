"""
============================================================
Article 6: From Prototype to Production — Churn ML Model
Days 19–25 of The Snowflake AI Practitioner's Playbook
============================================================
Series: https://github.com/yelpz04/snowflake-ai-practitioners-playbook
Folder: week-05-performance/python/

What this file covers (Article 6):
  - Train a churn prediction model using Snowpark ML
  - Features: call sentiment score, support ticket count, health score,
    days since last order, contract value
  - Store predictions to ANALYTICS.CUSTOMER_HEALTH_SCORES
  - Expose churn predictions to the Cortex Agent via the semantic view

Run order within week-05-performance/:
  - sql/qas_test_queries.sql          — warehouse tuning
  - sql/ai_observability_queries.sql  — cost/latency observability
  - python/churn_model.py             — THIS FILE — ML model training + scoring
  - sql/agent_usage_dashboard.sql     — usage dashboard

Prerequisites:
  - ANALYTICS.CUSTOMER_HEALTH_SCORES table exists
  - AI_OUTPUTS.CALL_AI_INSIGHTS populated (week-01-multimodal/python/audio_video_ai.py)
  - pip install snowflake-ml-python snowflake-snowpark-python

Docs: https://docs.snowflake.com/en/developer-guide/snowpark-ml/overview
============================================================
"""

from snowflake.snowpark import Session
from snowflake.ml.modeling.ensemble import RandomForestClassifier
from snowflake.ml.modeling.preprocessing import StandardScaler
from snowflake.ml.modeling.pipeline import Pipeline
import snowflake.ml.modeling.metrics as metrics

# ============================================================
# Session
# ============================================================

session = Session.builder.configs({
    "account": "YOUR_ACCOUNT",
    "user": "YOUR_USER",
    "authenticator": "externalbrowser",
    "database": "REVENUE_OPS_AI",
    "schema": "ANALYTICS",
    "warehouse": "REVOPS_AI_WH"
}).create()

# ============================================================
# Feature engineering — build training dataset
# ============================================================

training_df = session.sql("""
    SELECT
        c.CUSTOMER_ID,
        -- Call intelligence signals (from Article 2)
        COALESCE(AVG(ci.SENTIMENT_SCORE), 0.0)      AS avg_sentiment_score,
        COALESCE(MAX(ci.CHURN_RISK_SCORE), 0.0)     AS max_churn_signal,
        COUNT(ci.INSIGHT_ID)                         AS total_calls_analysed,
        -- Support signals
        COUNT(st.TICKET_ID)                          AS open_support_tickets,
        COALESCE(AVG(DATEDIFF('day', st.CREATED_DATE,
            COALESCE(st.RESOLVED_DATE, CURRENT_DATE()))), 0) AS avg_resolution_days,
        -- Order recency
        DATEDIFF('day', MAX(so.ORDER_DATE), CURRENT_DATE()) AS days_since_last_order,
        -- Customer profile
        COALESCE(SUM(so.TOTAL_AMOUNT), 0)            AS total_contract_value,
        c.INDUSTRY,
        c.COMPANY_SIZE,
        c.REGION,
        -- Label: churned within 90 days (1 = yes, 0 = no)
        CASE WHEN c.CHURNED_DATE IS NOT NULL
             AND c.CHURNED_DATE <= DATEADD('day', 90, CURRENT_DATE())
             THEN 1 ELSE 0 END                       AS churned_label
    FROM RAW.CUSTOMERS c
    LEFT JOIN AI_OUTPUTS.CALL_AI_INSIGHTS ci ON c.CUSTOMER_ID = ci.CUSTOMER_ID
    LEFT JOIN RAW.SUPPORT_TICKETS st
        ON c.CUSTOMER_ID = st.CUSTOMER_ID AND st.STATUS = 'OPEN'
    LEFT JOIN RAW.SALES_ORDERS so ON c.CUSTOMER_ID = so.CUSTOMER_ID
    WHERE c.CREATED_DATE <= DATEADD('day', -90, CURRENT_DATE())  -- only mature accounts
    GROUP BY c.CUSTOMER_ID, c.INDUSTRY, c.COMPANY_SIZE, c.REGION,
             c.CHURNED_DATE
""")

print(f"Training dataset: {training_df.count()} rows")

# ============================================================
# Train/test split and model pipeline
# ============================================================

feature_cols = [
    "AVG_SENTIMENT_SCORE", "MAX_CHURN_SIGNAL", "TOTAL_CALLS_ANALYSED",
    "OPEN_SUPPORT_TICKETS", "AVG_RESOLUTION_DAYS",
    "DAYS_SINCE_LAST_ORDER", "TOTAL_CONTRACT_VALUE"
]
label_col = "CHURNED_LABEL"

train_df, test_df = training_df.random_split([0.8, 0.2], seed=42)

pipeline = Pipeline(steps=[
    ("scaler", StandardScaler(input_cols=feature_cols, output_cols=feature_cols)),
    ("classifier", RandomForestClassifier(
        input_cols=feature_cols,
        label_cols=[label_col],
        output_cols=["CHURN_PREDICTION", "CHURN_PROBABILITY"],
        n_estimators=100,
        max_depth=6,
        random_state=42
    ))
])

pipeline.fit(train_df)

# ============================================================
# Evaluate
# ============================================================

predictions = pipeline.predict(test_df)
accuracy = metrics.accuracy_score(
    df=predictions,
    y_true_col_names=[label_col],
    y_pred_col_names=["CHURN_PREDICTION"]
)
print(f"Model accuracy: {accuracy:.1%}")

# ============================================================
# Score all active customers and write to CUSTOMER_HEALTH_SCORES
# ============================================================

all_customers = session.sql("""
    SELECT
        c.CUSTOMER_ID,
        c.CUSTOMER_NAME,
        COALESCE(AVG(ci.SENTIMENT_SCORE), 0.0)      AS avg_sentiment_score,
        COALESCE(MAX(ci.CHURN_RISK_SCORE), 0.0)     AS max_churn_signal,
        COUNT(ci.INSIGHT_ID)                         AS total_calls_analysed,
        COUNT(st.TICKET_ID)                          AS open_support_tickets,
        COALESCE(AVG(DATEDIFF('day', st.CREATED_DATE,
            COALESCE(st.RESOLVED_DATE, CURRENT_DATE()))), 0) AS avg_resolution_days,
        DATEDIFF('day', MAX(so.ORDER_DATE), CURRENT_DATE()) AS days_since_last_order,
        COALESCE(SUM(so.TOTAL_AMOUNT), 0)            AS total_contract_value,
        c.INDUSTRY,
        c.COMPANY_SIZE,
        c.REGION
    FROM RAW.CUSTOMERS c
    LEFT JOIN AI_OUTPUTS.CALL_AI_INSIGHTS ci ON c.CUSTOMER_ID = ci.CUSTOMER_ID
    LEFT JOIN RAW.SUPPORT_TICKETS st
        ON c.CUSTOMER_ID = st.CUSTOMER_ID AND st.STATUS = 'OPEN'
    LEFT JOIN RAW.SALES_ORDERS so ON c.CUSTOMER_ID = so.CUSTOMER_ID
    WHERE c.CHURNED_DATE IS NULL
    GROUP BY c.CUSTOMER_ID, c.CUSTOMER_NAME,
             c.INDUSTRY, c.COMPANY_SIZE, c.REGION
""")

scored = pipeline.predict(all_customers)

# Write predictions back as CUSTOMER_HEALTH_SCORES
scored.select(
    "CUSTOMER_ID",
    "CUSTOMER_NAME",
    "CHURN_PROBABILITY",
    "CHURN_PREDICTION",
    "AVG_SENTIMENT_SCORE",
    "OPEN_SUPPORT_TICKETS"
).with_column(
    "RISK_LEVEL",
    session.sql("""
        CASE
            WHEN CHURN_PROBABILITY >= 0.7 THEN 'High'
            WHEN CHURN_PROBABILITY >= 0.4 THEN 'Medium'
            ELSE 'Low'
        END
    """)
).write.mode("overwrite").save_as_table("ANALYTICS.CUSTOMER_HEALTH_SCORES")

print(f"Scored {scored.count()} active customers — written to CUSTOMER_HEALTH_SCORES")

# ============================================================
# Verify — top 10 highest churn risk customers
# ============================================================

session.sql("""
    SELECT CUSTOMER_ID, CUSTOMER_NAME, RISK_LEVEL,
           ROUND(CHURN_PROBABILITY * 100, 1) AS churn_pct,
           OPEN_SUPPORT_TICKETS,
           ROUND(AVG_SENTIMENT_SCORE, 2) AS sentiment
    FROM ANALYTICS.CUSTOMER_HEALTH_SCORES
    ORDER BY CHURN_PROBABILITY DESC
    LIMIT 10
""").show()
