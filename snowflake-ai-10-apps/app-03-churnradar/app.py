# ChurnRadar Streamlit app — removes unused altair import that caused ModuleNotFoundError
# Co-authored with CoCo
# ChurnRadar — Snowpark ML Churn Prediction + AI Explanations
# App 3 of 10: Snowpark ML + Cortex AI + Semantic Views

import streamlit as st
import pandas as pd
from snowflake.snowpark.context import get_active_session

session = get_active_session()

def cortex_complete(model, prompt):
    safe = prompt.replace("'", "''")
    return session.sql(f"SELECT SNOWFLAKE.CORTEX.COMPLETE('{model}', '{safe}')").collect()[0][0]

st.set_page_config(page_title="ChurnRadar", page_icon="📡", layout="wide")
st.title("📡 ChurnRadar AI Churn Prediction")
st.caption("Snowpark ML + Cortex AI —> trained and scored inside Snowflake")

tab1, tab2, tab3 = st.tabs(["🎯 Risk Dashboard", "🤖 Train Model", "💬 Ask Agent"])

FEATURE_COLS = ["DAYS_SINCE_LAST_ORDER", "OPEN_TICKETS", "AVG_SENTIMENT_SCORE",
                "CONTRACT_VALUE", "TOTAL_CALLS", "RESOLUTION_TIME_AVG"]

# ── TAB 1: Risk Dashboard ────────────────────────────────────────────────────
with tab1:
    risk_filter = st.selectbox("Filter by risk level:", ["All", "High", "Medium", "Low"])
    where = f"WHERE RISK_LEVEL = '{risk_filter}'" if risk_filter != "All" else ""

    customers = session.sql(f"""
        SELECT CUSTOMER_NAME, RISK_LEVEL,
               ROUND(CHURN_PROBABILITY * 100, 1) AS churn_pct,
               OPEN_TICKETS, DAYS_SINCE_ORDER,
               ROUND(AVG_SENTIMENT, 2) AS sentiment,
               SCORED_AT
        FROM FCX_PROD.SBX_DPP.CUSTOMER_HEALTH_SCORES
        {where}
        ORDER BY CHURN_PROBABILITY DESC
        LIMIT 50
    """).to_pandas()

    if customers.empty:
        st.info("No predictions yet. Train the model in the 'Train Model' tab first.")
    else:
        col1, col2, col3 = st.columns(3)
        high = customers[customers["RISK_LEVEL"] == "High"]
        col1.metric("High Risk", len(high), delta=f"⚠️ needs attention")
        col2.metric("Avg Churn Probability", f"{customers['CHURN_PCT'].mean():.1f}%")
        col3.metric("Customers Scored", len(customers))

        st.dataframe(customers, use_container_width=True,
                     column_config={"CHURN_PCT": st.column_config.ProgressColumn("Churn %", max_value=100)})

        # AI explanation on click
        st.divider()
        selected = st.selectbox("Get AI explanation for:", customers["CUSTOMER_NAME"].tolist())
        if selected:
            row = customers[customers["CUSTOMER_NAME"] == selected].iloc[0]
            with st.spinner("Generating AI action brief..."):
                explanation = cortex_complete(
                    "claude-sonnet-4-5",
                    f"""You are a customer success manager. Write a 3-bullet action brief.

Customer: {row['CUSTOMER_NAME']} | Churn probability: {row['CHURN_PCT']:.0f}%
Days since last order: {row['DAYS_SINCE_ORDER']}
Open tickets: {row['OPEN_TICKETS']}
Sentiment score: {row['SENTIMENT']} (range: -1 bad to +1 good)

Format: • [SIGNAL]: [RECOMMENDED ACTION]"""
                )
            st.markdown("#### Action Brief")
            st.write(explanation)

# ── TAB 2: Train Model ───────────────────────────────────────────────────────
with tab2:
    st.subheader("Train Churn Model (Snowpark ML)")
    st.info("Trains a RandomForestClassifier on your CUSTOMERS + ORDERS + SUPPORT + CALL data inside Snowflake.")

    n_estimators = st.slider("Number of trees", 50, 200, 100)
    max_depth    = st.slider("Max tree depth", 3, 10, 6)

    if st.button("🚀 Train & Score All Customers"):
        with st.spinner("Deploying training procedure to Snowflake..."):
            session.sql("""
CREATE OR REPLACE PROCEDURE FCX_PROD.SBX_DPP.TRAIN_CHURN_MODEL(N_ESTIMATORS INT, MAX_DEPTH INT)
RETURNS STRING
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('snowflake-snowpark-python', 'snowflake-ml-python')
HANDLER = 'train'
AS $$
def train(session, n_estimators, max_depth):
    from snowflake.ml.modeling.ensemble import RandomForestClassifier
    from snowflake.ml.modeling.preprocessing import StandardScaler
    from snowflake.snowpark import functions as F
    FEATURE_COLS = ['DAYS_SINCE_LAST_ORDER', 'OPEN_TICKETS', 'AVG_SENTIMENT_SCORE',
                    'CONTRACT_VALUE', 'TOTAL_CALLS', 'RESOLUTION_TIME_AVG']
    ml_features = session.table('FCX_PROD.SBX_DPP.ML_FEATURES')
    train_df, _ = ml_features.random_split([0.8, 0.2], seed=42)
    scaler = StandardScaler(input_cols=FEATURE_COLS, output_cols=FEATURE_COLS)
    scaler.fit(train_df)
    scaled_train = scaler.transform(train_df)
    scaled_all = scaler.transform(ml_features)
    clf = RandomForestClassifier(
        input_cols=FEATURE_COLS, label_cols=['CHURNED'],
        output_cols=['CHURN_PREDICTION'],
        n_estimators=n_estimators, max_depth=max_depth, random_state=42
    )
    clf.fit(scaled_train)
    proba_df = clf.predict_proba(scaled_all)
    known = set(c.upper() for c in scaled_all.columns)
    prob_cols = sorted([c for c in proba_df.columns if c.upper() not in known])
    churn_prob_col = prob_cols[-1]
    result = proba_df.select(
        'CUSTOMER_ID', 'CUSTOMER_NAME',
        F.col(churn_prob_col).alias('CHURN_PROBABILITY'),
        (F.col(churn_prob_col) >= 0.5).cast('BOOLEAN').alias('CHURN_PREDICTION'),
        'AVG_SENTIMENT_SCORE', 'OPEN_TICKETS', 'DAYS_SINCE_LAST_ORDER'
    )
    count = result.count()
    result.write.mode('overwrite').save_as_table('FCX_PROD.SBX_DPP.CUSTOMER_HEALTH_SCORES_STAGING')
    session.sql(
        'INSERT OVERWRITE INTO FCX_PROD.SBX_DPP.CUSTOMER_HEALTH_SCORES '
        'SELECT CUSTOMER_ID, CUSTOMER_NAME, '
        "CASE WHEN CHURN_PROBABILITY >= 0.7 THEN 'High' "
        "     WHEN CHURN_PROBABILITY >= 0.4 THEN 'Medium' "
        "     ELSE 'Low' END, "
        'CHURN_PROBABILITY, CHURN_PREDICTION, '
        'AVG_SENTIMENT_SCORE, OPEN_TICKETS, DAYS_SINCE_LAST_ORDER, '
        'NULL, CURRENT_TIMESTAMP() '
        'FROM FCX_PROD.SBX_DPP.CUSTOMER_HEALTH_SCORES_STAGING'
    ).collect()
    return f'Scored {count} customers'
$$
            """).collect()

        with st.spinner("Training model inside Snowflake..."):
            result = session.call("FCX_PROD.SBX_DPP.TRAIN_CHURN_MODEL", n_estimators, max_depth)
        st.success(f"✅ Model trained! {result}")


# ── TAB 3: Ask Agent ─────────────────────────────────────────────────────────
with tab3:
    st.subheader("Ask the Churn Agent")
    q = st.text_input("Ask anything about customer risk:",
                      placeholder="Which high-risk customers haven't been contacted in 30 days?")
    if q:
        with st.spinner("Analysing customer data..."):
            context_df = session.sql("""
                SELECT CUSTOMER_NAME, RISK_LEVEL,
                       ROUND(CHURN_PROBABILITY * 100, 1) AS CHURN_PCT,
                       OPEN_TICKETS, DAYS_SINCE_ORDER,
                       ROUND(AVG_SENTIMENT, 2) AS SENTIMENT
                FROM FCX_PROD.SBX_DPP.CUSTOMER_HEALTH_SCORES
                ORDER BY CHURN_PROBABILITY DESC
                LIMIT 20
            """).to_pandas()

        if context_df.empty:
            st.warning("No scored customers yet. Go to the **🤖 Train Model** tab and click **Train & Score All Customers** first, then come back to ask questions.")
        else:
            with st.spinner("Generating answer..."):
                answer = cortex_complete(
                    "claude-sonnet-4-5",
                    f"""You are a customer success analyst. Use the customer health data below to answer the question concisely.

CUSTOMER HEALTH DATA (top 20 by churn risk):
{context_df.to_string(index=False)}

QUESTION: {q}

Answer in plain English. Be specific — reference customer names and numbers from the data."""
                )
            st.write(answer)
