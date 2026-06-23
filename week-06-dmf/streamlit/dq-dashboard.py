"""
Streamlit Data Quality Dashboard
=========================================
A no-code/low-code DQ dashboard powered by DMF results.
Inspired by: https://adrianleexinhan.medium.com/building-a-no-code-data-quality-management-system-with-streamlit-and-snowflake-dmfs-and-genai-9458cec9c100
"""

import streamlit as st
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Data Quality Dashboard", layout="wide")
st.title("📊 Data Quality Dashboard")
st.caption("Powered by Snowflake Data Metric Functions + Anomaly Detection")

session = get_active_session()

# -- Sidebar --
st.sidebar.header("Filters")
days_back = st.sidebar.slider("Days to look back", 1, 90, 30)

# -- Overview Metrics --
st.subheader("Quality Overview")

overview = session.sql(f"""
    SELECT
        COUNT(DISTINCT TABLE_NAME) AS TABLES_MONITORED,
        COUNT(DISTINCT METRIC_NAME) AS METRICS_ACTIVE,
        COUNT(*) AS TOTAL_CHECKS,
        SUM(CASE WHEN IS_ANOMALY THEN 1 ELSE 0 END) AS TOTAL_ANOMALIES
    FROM SNOWFLAKE.LOCAL.DATA_QUALITY_MONITORING_RESULTS
    WHERE MEASUREMENT_TIME > DATEADD('day', -{days_back}, CURRENT_TIMESTAMP())
""").to_pandas()

if not overview.empty:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Tables Monitored", overview["TABLES_MONITORED"].iloc[0])
    col2.metric("Metrics Active", overview["METRICS_ACTIVE"].iloc[0])
    col3.metric("Total Checks", overview["TOTAL_CHECKS"].iloc[0])
    col4.metric("Anomalies Found", overview["TOTAL_ANOMALIES"].iloc[0])

# -- Table Health --
st.subheader("Table Health Status")

table_health = session.sql(f"""
    SELECT
        TABLE_SCHEMA,
        TABLE_NAME,
        COUNT(DISTINCT METRIC_NAME) AS METRICS,
        SUM(CASE WHEN IS_ANOMALY THEN 1 ELSE 0 END) AS ANOMALIES,
        MAX(MEASUREMENT_TIME) AS LAST_CHECK,
        CASE
            WHEN SUM(CASE WHEN IS_ANOMALY THEN 1 ELSE 0 END) = 0 THEN '✅ Healthy'
            WHEN SUM(CASE WHEN IS_ANOMALY THEN 1 ELSE 0 END) <= 2 THEN '⚠️ Warning'
            ELSE '🔴 Critical'
        END AS STATUS
    FROM SNOWFLAKE.LOCAL.DATA_QUALITY_MONITORING_RESULTS
    WHERE MEASUREMENT_TIME > DATEADD('day', -{days_back}, CURRENT_TIMESTAMP())
    GROUP BY 1, 2
    ORDER BY ANOMALIES DESC
""").to_pandas()

st.dataframe(table_health, use_container_width=True)

# -- Recent Anomalies --
st.subheader("Recent Anomalies")

anomalies = session.sql(f"""
    SELECT
        MEASUREMENT_TIME,
        TABLE_SCHEMA || '.' || TABLE_NAME AS TABLE_PATH,
        METRIC_NAME,
        VALUE,
        EXPECTED_RANGE_LOWER,
        EXPECTED_RANGE_UPPER,
        ANOMALY_SCORE
    FROM SNOWFLAKE.LOCAL.DATA_QUALITY_MONITORING_RESULTS
    WHERE IS_ANOMALY = TRUE
      AND MEASUREMENT_TIME > DATEADD('day', -{days_back}, CURRENT_TIMESTAMP())
    ORDER BY MEASUREMENT_TIME DESC
    LIMIT 50
""").to_pandas()

if not anomalies.empty:
    st.dataframe(anomalies, use_container_width=True)
else:
    st.success("No anomalies detected in the selected time range!")

# -- DMF Metric Trends --
st.subheader("Metric Trends")

tables = session.sql("""
    SELECT DISTINCT TABLE_SCHEMA || '.' || TABLE_NAME AS TABLE_PATH
    FROM SNOWFLAKE.LOCAL.DATA_QUALITY_MONITORING_RESULTS
    ORDER BY 1
""").collect()

selected_table = st.selectbox("Select Table", [t["TABLE_PATH"] for t in tables] if tables else [])

if selected_table:
    schema, table = selected_table.split(".")
    trend_data = session.sql(f"""
        SELECT
            DATE_TRUNC('day', MEASUREMENT_TIME) AS CHECK_DATE,
            METRIC_NAME,
            AVG(VALUE) AS AVG_VALUE,
            MAX(CASE WHEN IS_ANOMALY THEN 1 ELSE 0 END) AS HAD_ANOMALY
        FROM SNOWFLAKE.LOCAL.DATA_QUALITY_MONITORING_RESULTS
        WHERE TABLE_SCHEMA = '{schema}' AND TABLE_NAME = '{table}'
          AND MEASUREMENT_TIME > DATEADD('day', -{days_back}, CURRENT_TIMESTAMP())
        GROUP BY 1, 2
        ORDER BY 1
    """).to_pandas()

    if not trend_data.empty:
        for metric in trend_data["METRIC_NAME"].unique():
            metric_df = trend_data[trend_data["METRIC_NAME"] == metric]
            st.line_chart(metric_df.set_index("CHECK_DATE")["AVG_VALUE"])
            st.caption(f"Metric: {metric}")

# -- Footer --
st.divider()
st.caption("30 Days of Practical Snowflake AI POCs — Week 6: DMF + Production Readiness")
