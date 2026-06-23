"""
Streamlit in Snowflake Workspaces — Media + Feedback AI Analyzer
========================================================================
Deploy this app in Snowflake Workspaces (file-based workspace).
Docs: https://docs.snowflake.com/en/developer-guide/streamlit/streamlit-in-workspaces/streamlit-in-workspaces-overview

This app displays:
- Customer feedback with AI-derived sentiment
- Media file AI processing results (images, audio, video)
- Interactive filters by region, product line, sentiment
"""

import streamlit as st
from snowflake.snowpark.context import get_active_session

# -- App Config --
st.set_page_config(page_title="Revenue Ops AI Analyzer", layout="wide")
st.title("🔍 Revenue Ops AI Analyzer")
st.caption("Week 1 POC — Multimodal AI + Customer Feedback")

session = get_active_session()

# -- Sidebar Filters --
st.sidebar.header("Filters")

regions = session.sql("SELECT DISTINCT REGION FROM REVENUE_OPS_AI.RAW.CUSTOMERS ORDER BY 1").collect()
region_options = ["All"] + [r["REGION"] for r in regions]
selected_region = st.sidebar.selectbox("Region", region_options)

product_lines = session.sql("SELECT DISTINCT PRODUCT_CATEGORY FROM REVENUE_OPS_AI.RAW.SALES_ORDERS ORDER BY 1").collect()
product_options = ["All"] + [p["PRODUCT_CATEGORY"] for p in product_lines]
selected_product = st.sidebar.selectbox("Product Category", product_options)

# -- Tab Layout --
tab_feedback, tab_media, tab_calls, tab_video = st.tabs([
    "📝 Customer Feedback",
    "🖼️ Image AI Results",
    "🎙️ Call AI Insights",
    "🎬 Video AI Insights"
])

# ---- Customer Feedback ----
with tab_feedback:
    st.subheader("Customer Feedback Overview")

    feedback_query = "SELECT * FROM REVENUE_OPS_AI.RAW.CUSTOMER_FEEDBACK"
    filters = []
    if selected_region != "All":
        filters.append(f"REGION = '{selected_region}'")
    if selected_product != "All":
        filters.append(f"PRODUCT_LINE = '{selected_product}'")
    if filters:
        feedback_query += " WHERE " + " AND ".join(filters)
    feedback_query += " ORDER BY FEEDBACK_DATE DESC"

    feedback_df = session.sql(feedback_query).to_pandas()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Feedback", len(feedback_df))
    if not feedback_df.empty:
        col2.metric("Avg Rating", f"{feedback_df['RATING'].mean():.1f}")
        col3.metric("Low Ratings (≤2)", len(feedback_df[feedback_df["RATING"] <= 2]))

    st.dataframe(feedback_df, use_container_width=True)

# ---- Image AI Results ----
with tab_media:
    st.subheader("Image AI Processing Results")

    media_df = session.sql("""
        SELECT
            r.RESULT_ID,
            m.FILE_NAME,
            m.CONTEXT,
            m.CUSTOMER_ID,
            r.PROCESSING_TYPE,
            r.SUMMARY,
            r.PROCESSED_AT
        FROM REVENUE_OPS_AI.AI_OUTPUTS.MEDIA_AI_RESULTS r
        JOIN REVENUE_OPS_AI.RAW.MEDIA_FILES m ON r.FILE_ID = m.FILE_ID
        WHERE m.FILE_TYPE = 'image'
        ORDER BY r.PROCESSED_AT DESC
    """).to_pandas()

    st.dataframe(media_df, use_container_width=True)

    if not media_df.empty:
        selected_result = st.selectbox("View AI Output Detail", media_df["RESULT_ID"].tolist())
        if selected_result:
            detail = session.sql(f"""
                SELECT AI_OUTPUT
                FROM REVENUE_OPS_AI.AI_OUTPUTS.MEDIA_AI_RESULTS
                WHERE RESULT_ID = '{selected_result}'
            """).collect()
            if detail:
                st.json(detail[0]["AI_OUTPUT"])

# ---- Call AI Insights ----
with tab_calls:
    st.subheader("Call Recording AI Insights")

    calls_df = session.sql("""
        SELECT *
        FROM REVENUE_OPS_AI.AI_OUTPUTS.CALL_AI_INSIGHTS
        ORDER BY PROCESSED_AT DESC
    """).to_pandas()

    if not calls_df.empty:
        col1, col2 = st.columns(2)
        col1.metric("Total Calls Analyzed", len(calls_df))
        escalated = len(calls_df[calls_df["ESCALATION_DETECTED"] == True])
        col2.metric("Escalations Detected", escalated)

        st.dataframe(
            calls_df[["CUSTOMER_ID", "OVERALL_SENTIMENT", "SENTIMENT_SCORE",
                       "CUSTOMER_EMOTION", "ESCALATION_DETECTED", "CALL_SUMMARY"]],
            use_container_width=True
        )
    else:
        st.info("No call insights available yet. Run Day 3 audio analysis first.")

# ---- Video AI Insights ----
with tab_video:
    st.subheader("Video Content AI Insights")

    video_df = session.sql("""
        SELECT *
        FROM REVENUE_OPS_AI.AI_OUTPUTS.VIDEO_AI_INSIGHTS
        ORDER BY PROCESSED_AT DESC
    """).to_pandas()

    if not video_df.empty:
        for _, row in video_df.iterrows():
            with st.expander(f"📹 {row.get('FILE_ID', 'Video')} — Score: {row.get('MARKETING_QUALITY_SCORE', 'N/A')}/10"):
                st.write(f"**Summary:** {row.get('VIDEO_SUMMARY', 'N/A')}")
                st.write(f"**Tone:** {row.get('OVERALL_TONE', 'N/A')}")
                st.write(f"**Safety:** {row.get('CONTENT_SAFETY', 'N/A')}")
                st.write(f"**Audience:** {row.get('SUGGESTED_AUDIENCE', 'N/A')}")
    else:
        st.info("No video insights available yet. Run Day 4 video analysis first.")

# -- Footer --
st.divider()
st.caption("30 Days of Practical Snowflake AI POCs — Week 1: Media + Feedback AI Analyzer")
