# SQLGuardian — AI SQL Code Reviewer
# App 8 of 10: AI_COMPLETE + QUERY_HISTORY + structured review

import streamlit as st
import pandas as pd
import json
import hashlib
from snowflake.snowpark.context import get_active_session
from snowflake.cortex import Complete

session = get_active_session()
st.set_page_config(page_title="SQLGuardian", page_icon="🛡️", layout="wide")
st.title("🛡️ SQLGuardian — AI SQL Code Reviewer")
st.caption("Paste SQL → get structured review: performance, security, correctness, style")

REVIEW_PROMPT = """You are an expert Snowflake SQL reviewer. Analyse the SQL below and return ONLY valid JSON:
{
  "risk_score": <integer 1-10, 10 most risky>,
  "summary": "<one-sentence overall assessment>",
  "issues": [
    {
      "severity": "CRITICAL|WARNING|INFO",
      "category": "PERFORMANCE|SECURITY|CORRECTNESS|STYLE",
      "description": "<what the issue is>",
      "line_hint": "<relevant SQL fragment>",
      "recommendation": "<how to fix>"
    }
  ],
  "rewrite": "<improved SQL or null>"
}

Check for: Cartesian joins, SELECT *, missing WHERE on large scans, no LIMIT, NULL handling errors,
implicit type casts, dynamic SQL injection risk, unmasked sensitive columns, GROUP BY inconsistencies.

SQL:
"""

SEVERITY_COLOURS = {"CRITICAL": "🔴", "WARNING": "🟠", "INFO": "🔵"}
CATEGORY_ICONS   = {"PERFORMANCE": "⚡", "SECURITY": "🔒", "CORRECTNESS": "✅", "STYLE": "✍️"}

tab1, tab2, tab3 = st.tabs(["🔍 Review SQL", "📊 Query History", "📈 Risk Trends"])

# ── TAB 1: Review SQL ────────────────────────────────────────────────────────
with tab1:
    sql_input = st.text_area("Paste your SQL here:", height=200, placeholder="SELECT * FROM orders WHERE ...")

    c1, c2 = st.columns([1, 3])
    with c1:
        review_btn = st.button("🤖 Review SQL", type="primary")
    with c2:
        st.caption("Checks: Cartesian joins, SELECT *, missing filters, NULL handling, security risks")

    if review_btn and sql_input.strip():
        with st.spinner("AI is reviewing your SQL..."):
            raw = Complete("claude-sonnet-4-5", REVIEW_PROMPT + sql_input)

        try:
            review = json.loads(raw)
        except Exception:
            st.error("Could not parse AI response. Raw output:")
            st.code(raw)
            st.stop()

        risk = review.get("risk_score", 0)
        issues = review.get("issues", [])
        has_critical = any(i.get("severity") == "CRITICAL" for i in issues)

        # Risk score display
        col1, col2, col3 = st.columns(3)
        risk_colour = "🔴" if risk >= 7 else "🟠" if risk >= 4 else "🟢"
        col1.metric("Risk Score", f"{risk_colour} {risk}/10")
        col2.metric("Issues Found", len(issues))
        col3.metric("Critical Issues", sum(1 for i in issues if i.get("severity") == "CRITICAL"))

        if review.get("summary"):
            st.info(f"**Summary:** {review['summary']}")

        if issues:
            st.divider()
            st.subheader("Issues")
            for issue in sorted(issues, key=lambda x: ["CRITICAL","WARNING","INFO"].index(x.get("severity","INFO"))):
                sev  = issue.get("severity", "INFO")
                cat  = issue.get("category", "")
                icon = f"{SEVERITY_COLOURS.get(sev,'⚪')} {CATEGORY_ICONS.get(cat,'')}"
                with st.expander(f"{icon} [{sev}] {cat} — {issue.get('description','')[:80]}"):
                    if issue.get("line_hint"):
                        st.code(issue["line_hint"], language="sql")
                    st.write(f"**Recommendation:** {issue.get('recommendation','')}")
        else:
            st.success("✅ No issues found!")

        if review.get("rewrite"):
            st.divider()
            st.subheader("Suggested Rewrite")
            st.code(review["rewrite"], language="sql")

        # Save to history
        sql_hash = hashlib.sha256(sql_input.encode()).hexdigest()[:16]
        safe_json = json.dumps(review).replace("'", "''")
        session.sql(f"""
            INSERT INTO SQLGUARDIAN.PUBLIC.REVIEW_HISTORY
                (SQL_HASH, RISK_SCORE, ISSUE_COUNT, HAS_CRITICAL, REVIEW_JSON)
            SELECT '{sql_hash}', {risk}, {len(issues)}, {'TRUE' if has_critical else 'FALSE'},
                   PARSE_JSON('{safe_json}')
        """).collect()

# ── TAB 2: Query History ─────────────────────────────────────────────────────
with tab2:
    st.subheader("Your Most Expensive Queries (Last 7 Days)")
    days_back = st.slider("Days to look back:", 1, 30, 7)

    expensive = session.sql(f"""
        SELECT LEFT(QUERY_TEXT, 200) AS query_preview,
               ROUND(BYTES_SCANNED / 1e9, 2) AS gb_scanned,
               ROUND(TOTAL_ELAPSED_TIME / 1000.0, 1) AS seconds,
               QUERY_TYPE, START_TIME
        FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
        WHERE EXECUTION_STATUS = 'SUCCESS'
          AND BYTES_SCANNED > 5e8
          AND START_TIME > DATEADD(day, -{days_back}, CURRENT_TIMESTAMP())
        ORDER BY BYTES_SCANNED DESC LIMIT 20
    """).to_pandas()

    if expensive.empty:
        st.info("No expensive queries found in the selected period.")
    else:
        st.dataframe(expensive, use_container_width=True)
        selected_idx = st.selectbox("Select a query to review:", expensive.index,
                                     format_func=lambda i: expensive.loc[i, "QUERY_PREVIEW"][:80])
        if st.button("🤖 Review selected query"):
            sql_to_review = session.sql(f"""
                SELECT QUERY_TEXT FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
                WHERE LEFT(QUERY_TEXT, 200) = '{expensive.loc[selected_idx, "QUERY_PREVIEW"].replace("'", "''")}'
                LIMIT 1
            """).collect()[0][0]
            st.text_area("Full query:", sql_to_review, height=150)
            st.session_state["question_input"] = sql_to_review

# ── TAB 3: Risk Trends ───────────────────────────────────────────────────────
with tab3:
    trends = session.sql(
        "SELECT week, avg_risk_score, reviews, critical_reviews FROM SQLGUARDIAN.PUBLIC.RISK_TREND"
    ).to_pandas()
    if trends.empty:
        st.info("No review history yet. Submit some SQL reviews to see trends.")
    else:
        import altair as alt
        st.altair_chart(
            alt.Chart(trends).mark_line(point=True).encode(
                x="week:T", y=alt.Y("avg_risk_score:Q", scale=alt.Scale(domain=[0,10])),
                tooltip=["week:T", "avg_risk_score:Q", "reviews:Q", "critical_reviews:Q"]
            ).properties(title="Average Risk Score Over Time", height=300),
            use_container_width=True
        )
