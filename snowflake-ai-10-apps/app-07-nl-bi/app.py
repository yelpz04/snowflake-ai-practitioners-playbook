# NL-BI — Natural Language Business Intelligence
# App 7 of 10: Cortex Analyst + Semantic Views + auto-chart

import streamlit as st
import pandas as pd
import altair as alt
import json
from snowflake.snowpark.context import get_active_session
from snowflake.cortex import Complete

session = get_active_session()
st.set_page_config(page_title="NL-BI", page_icon="📊", layout="wide")
st.title("📊 NL-BI — Ask Your Data Anything")
st.caption("Cortex Analyst + Semantic Views — type a question, get a verified SQL chart")

if "history" not in st.session_state:
    st.session_state.history = []

EXAMPLE_QUESTIONS = [
    "Which product category had the highest revenue last month?",
    "Show me weekly revenue trend for the last 3 months",
    "Which region has the most orders but lowest average order value?",
    "What percentage of orders are from North America?",
    "Compare total revenue by country for this quarter vs last quarter",
]

def auto_chart(df: pd.DataFrame):
    if df.empty or len(df.columns) < 2:
        st.dataframe(df, use_container_width=True)
        return
    cols = df.columns.tolist()
    first_is_date  = pd.api.types.is_datetime64_any_dtype(df[cols[0]])
    second_is_num  = pd.api.types.is_numeric_dtype(df[cols[1]])

    if first_is_date and second_is_num and len(cols) == 2:
        st.altair_chart(alt.Chart(df).mark_line(point=True).encode(
            x=alt.X(cols[0], title=cols[0]),
            y=alt.Y(cols[1], title=cols[1])
        ).properties(height=350).interactive(), use_container_width=True)
    elif len(cols) == 2 and second_is_num:
        st.altair_chart(alt.Chart(df).mark_bar().encode(
            x=alt.X(cols[1], title=cols[1]),
            y=alt.Y(cols[0], sort="-x", title=cols[0]),
            tooltip=cols
        ).properties(height=max(200, len(df) * 35)).interactive(), use_container_width=True)
    elif len(cols) == 3 and pd.api.types.is_numeric_dtype(df[cols[2]]):
        st.altair_chart(alt.Chart(df).mark_bar().encode(
            x=cols[0], y=alt.Y(cols[2], title=cols[2]),
            color=cols[1], tooltip=cols
        ).properties(height=350).interactive(), use_container_width=True)
    else:
        st.dataframe(df, use_container_width=True)

with st.expander("💡 Example questions", expanded=False):
    for eq in EXAMPLE_QUESTIONS:
        if st.button(eq, key=f"ex_{eq[:20]}"):
            st.session_state["question_input"] = eq

question = st.text_input(
    "Ask your data a question:",
    value=st.session_state.get("question_input", ""),
    placeholder="Which region had the highest revenue last quarter?",
    key="main_question"
)

show_sql = st.checkbox("Show generated SQL", value=True)

if question and st.button("▶ Get Answer"):
    with st.spinner("Cortex Analyst is generating SQL..."):
        try:
            analyst_result = session.sql("""
                SELECT SNOWFLAKE.CORTEX.ANALYST(
                    @NL_BI.PUBLIC.ANALYST_STAGE/sales_intelligence.yaml,
                    :1
                )
            """, params=[question]).collect()[0][0]

            parsed = json.loads(analyst_result) if isinstance(analyst_result, str) else analyst_result
            generated_sql = parsed.get("sql", "")
            explanation   = parsed.get("explanation", "")

        except Exception as e:
            # Fallback: use AI_COMPLETE to generate SQL
            st.warning("Cortex Analyst stage not found — using AI_COMPLETE fallback.")
            generated_sql = Complete(
                "claude-sonnet-4-5",
                f"""You are a Snowflake SQL expert. The user has this schema:
Tables: NL_BI.PUBLIC.ORDERS (ORDER_ID, ORDER_DATE, CUSTOMER_ID, PRODUCT_ID, REGION_ID, ORDER_VALUE, QUANTITY, STATUS),
NL_BI.PUBLIC.PRODUCTS (PRODUCT_ID, PRODUCT_NAME, CATEGORY, UNIT_PRICE),
NL_BI.PUBLIC.REGIONS (REGION_ID, REGION_NAME, COUNTRY)
Write ONLY a valid SELECT SQL query to answer: {question}
Return ONLY the SQL, no explanation."""
            )
            explanation = ""

        if show_sql and generated_sql:
            with st.expander("Generated SQL", expanded=False):
                st.code(generated_sql, language="sql")
        if explanation:
            st.caption(f"💬 {explanation}")

        try:
            df = session.sql(generated_sql).to_pandas()
            auto_chart(df)
            st.session_state.history.append({
                "question": question, "sql": generated_sql, "rows": len(df)
            })
        except Exception as err:
            st.error(f"Query execution error: {err}")

if st.session_state.history:
    with st.expander(f"📜 Session history ({len(st.session_state.history)} questions)", expanded=False):
        for item in reversed(st.session_state.history):
            st.markdown(f"**Q:** {item['question']} → {item['rows']} rows")
