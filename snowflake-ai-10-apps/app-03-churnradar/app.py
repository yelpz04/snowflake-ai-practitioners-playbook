# ChurnRadar — Snowpark ML Churn Prediction + AI Explanations
# App 3 of 10: Snowpark ML + Cortex AI + Semantic Views

import streamlit as st
import pandas as pd
import altair as alt
from snowflake.snowpark.context import get_active_session
from snowflake.cortex import Complete
from snowflake.ml.modeling.ensemble import RandomForestClassifier
from snowflake.ml.modeling.preprocessing import StandardScaler
from snowflake.ml.modeling.pipeline import Pipeline

session = get_active_session()

st.set_page_config(page_title="ChurnRadar", page_icon="📡", layout="wide")
st.title("📡 ChurnRadar — AI Churn Prediction")
st.caption("Snowpark ML + Cortex AI — trained and scored inside Snowflake")

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
        FROM CHURNRADAR.PUBLIC.CUSTOMER_HEALTH_SCORES
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
                explanation = Complete(
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
        with st.spinner("Training model inside Snowflake..."):
            df = session.table("CHURNRADAR.PUBLIC.ML_FEATURES")
            train_df, test_df = df.random_split([0.8, 0.2], seed=42)

            pipe = Pipeline(steps=[
                ("scaler", StandardScaler(input_cols=FEATURE_COLS, output_cols=FEATURE_COLS)),
                ("model",  RandomForestClassifier(
                    input_cols=FEATURE_COLS, label_cols=["CHURNED"],
                    output_cols=["CHURN_PREDICTION", "CHURN_PROBABILITY"],
                    n_estimators=n_estimators, max_depth=max_depth, random_state=42
                ))
            ])
            pipe.fit(train_df)

            # Score all customers
            all_df = session.table("CHURNRADAR.PUBLIC.ML_FEATURES")
            scored = pipe.predict(all_df)

            # Write to CUSTOMER_HEALTH_SCORES
            scored.select(
                "CUSTOMER_ID", "CUSTOMER_NAME",
                (scored["CHURN_PROBABILITY"] >= 0.7).cast("STRING").alias("RISK_LEVEL_RAW"),
                "CHURN_PROBABILITY", "CHURN_PREDICTION",
                "AVG_SENTIMENT_SCORE", "OPEN_TICKETS", "DAYS_SINCE_LAST_ORDER"
            ).write.mode("overwrite").save_as_table("CHURNRADAR.PUBLIC.CUSTOMER_HEALTH_SCORES_STAGING")

            session.sql("""
                INSERT OVERWRITE INTO CHURNRADAR.PUBLIC.CUSTOMER_HEALTH_SCORES
                SELECT CUSTOMER_ID, CUSTOMER_NAME,
                       CASE WHEN CHURN_PROBABILITY >= 0.7 THEN 'High'
                            WHEN CHURN_PROBABILITY >= 0.4 THEN 'Medium'
                            ELSE 'Low' END,
                       CHURN_PROBABILITY, CHURN_PREDICTION,
                       AVG_SENTIMENT_SCORE, OPEN_TICKETS, DAYS_SINCE_LAST_ORDER,
                       NULL, CURRENT_TIMESTAMP()
                FROM CHURNRADAR.PUBLIC.CUSTOMER_HEALTH_SCORES_STAGING
            """).collect()

            st.success(f"✅ Model trained and {scored.count()} customers scored!")

# ── TAB 3: Ask Agent ─────────────────────────────────────────────────────────
with tab3:
    st.subheader("Ask the Churn Agent")
    q = st.text_input("Ask anything about customer risk:",
                      placeholder="Which high-risk customers haven't been contacted in 30 days?")
    if q:
        with st.spinner("Agent is querying..."):
            answer = session.sql(f"""
                SELECT SNOWFLAKE.CORTEX.AGENT_COMPLETE(
                    'CHURNRADAR_AGENT',
                    '{q.replace("'", "''")}')
            """).collect()[0][0]
        st.write(answer)
