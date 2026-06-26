# SnowCost AI — Streamlit in Snowflake App

import streamlit as st
import pandas as pd
import altair as alt
from snowflake.snowpark.context import get_active_session

session = get_active_session()

def Complete(model, prompt):
    return session.sql(
        "SELECT SNOWFLAKE.CORTEX.COMPLETE(?, ?)", params=[model, prompt]
    ).collect()[0][0]

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="SnowCost AI", page_icon="❄️", layout="wide")
st.title("❄️ SnowCost AI")
st.caption("Natural language Snowflake cost intelligence — powered by Cortex Analyst + AI_COMPLETE")
st.info("Data from ACCOUNT_USAGE has a ~3 hour lag. Costs shown are approximate.", icon="ℹ️")

# ── Sidebar filters ──────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filters")
    days_back = st.slider("Look-back window (days)", 7, 90, 30)
    show_anomalies = st.toggle("Show anomalies only", False)
    st.divider()
    st.caption("App 1 of 10 — Practical Snowflake AI Apps")

# ── Tab layout ───────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["💬 Ask a Question", "📊 Cost Dashboard", "🚨 Anomalies"])

# ── TAB 1: Cortex Analyst natural language ───────────────────────────────────
with tab1:
    st.subheader("Ask anything about your Snowflake costs")
    st.caption("Powered by Cortex Analyst — no SQL needed")

    example_questions = [
        "Which warehouses had the highest TOTAL_CREDITS_USED in the last 7 days?",
        "Show me daily TOTAL_CREDITS_USED trend for the past 30 days",
        "Which warehouse has the highest TOTAL_CLOUD_SERVICES_CREDITS_USED this month?",
        "What was our peak TOTAL_COMPUTE_CREDITS_USED hour this month?",
    ]
    selected = st.selectbox("Try an example:", [""] + example_questions)
    question = st.text_input("Or type your own question:", value=selected)

    if question:
        with st.spinner("Cortex Analyst is generating SQL..."):
            try:
                # Cortex Analyst: natural language → SQL → results
                analyst_result = session.sql(f"""
                    SELECT SNOWFLAKE.CORTEX.ANALYST_QUERY(
                        'SNOWCOST_AI.PUBLIC.SNOWCOST_AI_SV',
                        '{question.replace("'", "''")}'
                    )
                """).collect()[0][0]

                import json
                result_json = json.loads(analyst_result)
                generated_sql = result_json.get("sql", "")

                if generated_sql:
                    with st.expander("Generated SQL", expanded=False):
                        st.code(generated_sql, language="sql")

                    df = session.sql(generated_sql).to_pandas()
                    st.dataframe(df, use_container_width=True)

                    # Auto-chart if there's a numeric + date column
                    date_cols = [c for c in df.columns if "date" in c.lower() or "time" in c.lower()]
                    num_cols  = [c for c in df.columns if df[c].dtype in ["float64", "int64"]]
                    if date_cols and num_cols:
                        chart = alt.Chart(df).mark_line(point=True).encode(
                            x=alt.X(date_cols[0], title="Date"),
                            y=alt.Y(num_cols[0], title=num_cols[0]),
                            color=alt.Color("WAREHOUSE_NAME:N") if "WAREHOUSE_NAME" in df.columns else alt.value("steelblue")
                        ).properties(height=300)
                        st.altair_chart(chart, use_container_width=True)
                else:
                    st.warning("Cortex Analyst could not generate SQL for this question. Try rephrasing.")

            except Exception as e:
                st.error(f"Error: {e}")

# ── TAB 2: Cost Dashboard ────────────────────────────────────────────────────
with tab2:
    st.subheader(f"Cost Overview — Last {days_back} Days")

    # Top warehouses by spend
    top_wh = session.sql(f"""
        SELECT WAREHOUSE_NAME,
               ROUND(SUM(total_credits), 2) AS total_credits,
               ROUND(SUM(compute_credits), 2) AS compute,
               ROUND(SUM(cloud_service_credits), 2) AS cloud_services
        FROM SNOWCOST_AI.PUBLIC.DAILY_WAREHOUSE_COSTS
        WHERE cost_date >= DATEADD('day', -{days_back}, CURRENT_DATE())
        GROUP BY WAREHOUSE_NAME
        ORDER BY total_credits DESC
        LIMIT 10
    """).to_pandas()

    col1, col2, col3 = st.columns(3)
    if not top_wh.empty:
        col1.metric("Total Credits", f"{top_wh['TOTAL_CREDITS'].sum():.1f}")
        col2.metric("Top Warehouse", top_wh.iloc[0]["WAREHOUSE_NAME"])
        col3.metric("Top Warehouse Credits", f"{top_wh.iloc[0]['TOTAL_CREDITS']:.1f}")

    bar = alt.Chart(top_wh).mark_bar().encode(
        x=alt.X("TOTAL_CREDITS:Q", title="Credits"),
        y=alt.Y("WAREHOUSE_NAME:N", sort="-x", title="Warehouse"),
        color=alt.value("#29B5E8"),
        tooltip=["WAREHOUSE_NAME", "TOTAL_CREDITS", "COMPUTE", "CLOUD_SERVICES"]
    ).properties(height=300, title="Credits by Warehouse")
    st.altair_chart(bar, use_container_width=True)

    # Daily trend
    daily = session.sql(f"""
        SELECT cost_date, ROUND(SUM(total_credits), 2) AS daily_credits
        FROM SNOWCOST_AI.PUBLIC.DAILY_WAREHOUSE_COSTS
        WHERE cost_date >= DATEADD('day', -{days_back}, CURRENT_DATE())
        GROUP BY cost_date ORDER BY cost_date
    """).to_pandas()

    line = alt.Chart(daily).mark_area(opacity=0.4, line=True).encode(
        x=alt.X("cost_date:T", title="Date"),
        y=alt.Y("daily_credits:Q", title="Credits"),
        color=alt.value("#29B5E8")
    ).properties(height=200, title="Daily Credit Spend")
    st.altair_chart(line, use_container_width=True)

    # Warehouses with no resource monitor
    # RESOURCE_MONITOR_GAPS is a static TABLE — refresh via button or daily task
    st.divider()
    col_gap1, col_gap2 = st.columns([3, 1])
    col_gap1.markdown("**Resource Monitor Coverage**")
    if col_gap2.button("🔄 Refresh Now", help="Runs SHOW WAREHOUSES and repopulates the table"):
        with st.spinner("Refreshing warehouse data..."):
            try:
                session.sql("SHOW WAREHOUSES").collect()
                session.sql("""
                    INSERT OVERWRITE INTO SNOWCOST_AI.PUBLIC.RESOURCE_MONITOR_GAPS
                    SELECT
                        \"name\", \"size\", \"type\", \"auto_suspend\", \"resource_monitor\",
                        CASE WHEN \"resource_monitor\" IS NULL OR \"resource_monitor\" = 'null'
                             THEN 'NO MONITOR' ELSE 'MONITORED' END
                    FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))
                """).collect()
                st.success("Refreshed.")
            except Exception as e:
                st.error(f"Refresh failed: {e}")

    gaps = session.sql("""
        SELECT WAREHOUSE_NAME, WAREHOUSE_SIZE, WAREHOUSE_TYPE,
               AUTO_SUSPEND_SECONDS, RESOURCE_MONITOR, MONITOR_STATUS
        FROM SNOWCOST_AI.PUBLIC.RESOURCE_MONITOR_GAPS
        WHERE MONITOR_STATUS = 'NO MONITOR'
    """).to_pandas()
    if gaps.empty:
        st.success("✅ All warehouses have a resource monitor — or table not yet populated (click Refresh).")
    else:
        st.warning(f"⚠️ {len(gaps)} warehouses have no resource monitor:")
        st.dataframe(gaps, use_container_width=True)

# ── TAB 3: AI-Explained Anomalies ───────────────────────────────────────────
with tab3:
    st.subheader("Cost Anomalies — AI Explained")
    st.caption("Z-score > 2σ from 30-day rolling average. Explanations generated by claude-sonnet-4-5.")

    anomalies = session.sql("""
        SELECT cost_date, WAREHOUSE_NAME, total_credits,
               avg_credits, z_score, anomaly_level
        FROM SNOWCOST_AI.PUBLIC.COST_ANOMALIES
        ORDER BY z_score DESC
        LIMIT 20
    """).to_pandas()

    if anomalies.empty:
        st.success("✅ No cost anomalies detected in the last 7 days.")
    else:
        st.error(f"🚨 {len(anomalies)} anomalies detected")

        for _, row in anomalies.iterrows():
            level_icon = "🔴" if row["ANOMALY_LEVEL"] == "CRITICAL" else "🟡"
            with st.expander(
                f"{level_icon} {row['WAREHOUSE_NAME']} — {row['TOTAL_CREDITS']:.1f} credits "
                f"({row['Z_SCORE']:.1f}σ above average) on {row['COST_DATE']}"
            ):
                col1, col2 = st.columns(2)
                col1.metric("Credits Used", f"{row['TOTAL_CREDITS']:.1f}")
                col2.metric("30-day Average", f"{row['AVG_CREDITS']:.1f}")

                with st.spinner("AI is explaining this anomaly..."):
                    explanation = Complete(
                        "claude-sonnet-4-5",
                        f"""You are a Snowflake FinOps advisor. Be concise.
                        
Warehouse '{row['WAREHOUSE_NAME']}' used {row['TOTAL_CREDITS']:.1f} credits on {row['COST_DATE']}.
30-day average: {row['AVG_CREDITS']:.1f} credits. Z-score: {row['Z_SCORE']:.1f}.

Respond in exactly this format:
EXPLANATION: [one sentence explaining likely cause]
ACTION: [one specific remediation step]"""
                    )

                parts = explanation.split("ACTION:")
                if len(parts) == 2:
                    exp_text = parts[0].replace("EXPLANATION:", "").strip()
                    act_text = parts[1].strip()
                    st.info(f"**Why:** {exp_text}")
                    st.success(f"**Action:** {act_text}")
                else:
                    st.write(explanation)
