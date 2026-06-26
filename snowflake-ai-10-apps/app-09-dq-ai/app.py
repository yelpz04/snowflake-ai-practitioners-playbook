# DQ-AI — Self-Healing Data Quality Dashboard
# App 9 of 10: DMF + AI_COMPLETE + Snowflake Tasks

import streamlit as st
import pandas as pd
import altair as alt
from snowflake.snowpark.context import get_active_session
from snowflake.cortex import Complete

session = get_active_session()
st.set_page_config(page_title="DQ-AI", page_icon="🩺", layout="wide")
st.title("🩺 DQ-AI — Self-Healing Data Quality")
st.caption("DMF + AI_COMPLETE + Snowflake Tasks — detects, explains, and fixes data issues")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Health Dashboard", "🚨 Alert Inbox", "🔧 Quarantine", "📈 Trends"])

# ── TAB 1: Health Dashboard ──────────────────────────────────────────────────
with tab1:
    results = session.sql("""
        SELECT TABLE_NAME, METRIC_NAME,
               ROUND(AVG(METRIC_VALUE), 2) AS avg_value,
               MAX(METRIC_VALUE) AS max_value,
               MAX(MEASUREMENT_TIME) AS last_checked,
               SUM(CASE WHEN METRIC_VALUE > 0 THEN 1 ELSE 0 END) AS failure_count,
               COUNT(*) AS total_checks
        FROM SNOWFLAKE.LOCAL.DATA_QUALITY_MONITORING_RESULTS
        WHERE MEASUREMENT_TIME > DATEADD(day, -7, CURRENT_TIMESTAMP())
        GROUP BY TABLE_NAME, METRIC_NAME
        ORDER BY failure_count DESC
    """).to_pandas()

    if results.empty:
        st.info("No DMF results found. Attach DMFs to tables (see setup.sql).")
    else:
        total = len(results)
        failing = results[results["FAILURE_COUNT"] > 0]

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Tables Monitored", results["TABLE_NAME"].nunique())
        col2.metric("Checks Configured", total)
        col3.metric("Currently Failing", len(failing), delta=f"⚠️" if len(failing) else "✅")
        col4.metric("Pass Rate", f"{(1 - len(failing)/total)*100:.0f}%" if total else "N/A")

        for table in results["TABLE_NAME"].unique():
            t_df = results[results["TABLE_NAME"] == table]
            failed = t_df[t_df["FAILURE_COUNT"] > 0]
            icon = "🔴" if len(failed) > 0 else "🟢"
            with st.expander(f"{icon} {table} — {len(failed)}/{len(t_df)} checks failing"):
                st.dataframe(t_df[["METRIC_NAME","avg_value","max_value","failure_count","last_checked"]],
                             use_container_width=True)

# ── TAB 2: Alert Inbox ───────────────────────────────────────────────────────
with tab2:
    unacked = session.sql("""
        SELECT ALERT_ID, TABLE_NAME, METRIC_NAME, FAILURE_VALUE,
               SEVERITY, LEFT(AI_EXPLANATION, 300) AS explanation, CREATED_AT
        FROM DQ_AI.PUBLIC.DQ_AI_ALERTS
        WHERE NOT ACKNOWLEDGED
        ORDER BY CASE SEVERITY WHEN 'CRITICAL' THEN 1 WHEN 'WARNING' THEN 2 ELSE 3 END, CREATED_AT DESC
        LIMIT 50
    """).to_pandas()

    if unacked.empty:
        st.success("✅ No unacknowledged alerts.")
    else:
        st.warning(f"{len(unacked)} unacknowledged alerts")
        for _, row in unacked.iterrows():
            sev_icon = {"CRITICAL": "🔴", "WARNING": "🟠", "INFO": "🔵"}.get(row["SEVERITY"], "⚪")
            with st.expander(f"{sev_icon} [{row['SEVERITY']}] {row['TABLE_NAME']}.{row['METRIC_NAME']} — {row['CREATED_AT']}"):
                st.write(f"**Value:** {row['FAILURE_VALUE']}")
                st.info(f"**AI Explanation:** {row['EXPLANATION']}")
                if st.button("✓ Acknowledge", key=f"ack_{row['ALERT_ID']}"):
                    session.sql(f"UPDATE DQ_AI.PUBLIC.DQ_AI_ALERTS SET ACKNOWLEDGED = TRUE WHERE ALERT_ID = '{row['ALERT_ID']}'").collect()
                    st.rerun()

    if st.button("🤖 Run AI Alert Enrichment Now"):
        with st.spinner("Fetching new DMF failures and enriching with AI..."):
            session.sql("EXECUTE TASK DQ_AI.PUBLIC.ENRICH_ALERTS").collect()
            st.success("Alert enrichment task executed.")

# ── TAB 3: Quarantine ────────────────────────────────────────────────────────
with tab3:
    q_rows = session.sql("""
        SELECT ORDER_ID, CUSTOMER_ID, ORDER_DATE, AMOUNT,
               QUARANTINE_REASON, QUARANTINED_AT
        FROM DQ_AI.PUBLIC.QUARANTINE_ORDERS
        ORDER BY QUARANTINED_AT DESC LIMIT 200
    """).to_pandas()

    col1, col2 = st.columns(2)
    col1.metric("Quarantined Rows", len(q_rows))
    remediation = session.sql(
        "SELECT SUM(ROWS_AFFECTED) AS total FROM DQ_AI.PUBLIC.REMEDIATION_LOG"
    ).collect()[0][0]
    col2.metric("Total Auto-Remediated", remediation or 0)

    if not q_rows.empty:
        st.dataframe(q_rows, use_container_width=True)
        if st.button("🔁 Reprocess (clear NULL CUSTOMER_ID rows)"):
            session.sql("DELETE FROM DQ_AI.PUBLIC.QUARANTINE_ORDERS WHERE QUARANTINE_REASON = 'NULL_CUSTOMER_ID'").collect()
            st.success("Quarantine cleared.")

# ── TAB 4: Trends ────────────────────────────────────────────────────────────
with tab4:
    trend = session.sql("""
        SELECT DATE_TRUNC('day', MEASUREMENT_TIME) AS day,
               COUNT(*) AS total_checks,
               SUM(CASE WHEN METRIC_VALUE > 0 THEN 1 ELSE 0 END) AS failures
        FROM SNOWFLAKE.LOCAL.DATA_QUALITY_MONITORING_RESULTS
        WHERE MEASUREMENT_TIME > DATEADD(day, -30, CURRENT_TIMESTAMP())
        GROUP BY 1 ORDER BY 1
    """).to_pandas()

    if not trend.empty:
        trend["pass_rate"] = ((trend["total_checks"] - trend["failures"]) / trend["total_checks"] * 100).round(1)
        st.altair_chart(
            alt.Chart(trend).mark_area(opacity=0.6).encode(
                x="day:T", y=alt.Y("pass_rate:Q", scale=alt.Scale(domain=[0,100])),
                tooltip=["day:T","pass_rate:Q","failures:Q"]
            ).properties(title="Daily Data Quality Pass Rate (%)", height=300),
            use_container_width=True
        )
