# Cortex Guard — Enterprise AI Safety in One Boolean Flag
# Reference: https://medium.com/@beingabhishekmittal/guardrails-not-guesswork-the-complete-guide-to-cortex-guard-and-enterprise-ai-safety-8076e9405575

import streamlit as st
from snowflake.cortex import complete, CompleteOptions
from snowflake.snowpark.context import get_active_session

session = get_active_session()

st.title("🛡️ Cortex Guard Demo — Revenue Ops AI")
st.caption("Enterprise AI Safety with guardrails: true")

# ============================================================
# 1. Guarded vs Unguarded side-by-side
# ============================================================
user_input = st.text_area("Enter a prompt to test:", value="Summarize Q1 revenue trends by region")

col1, col2 = st.columns(2)

with col1:
    st.subheader("🔓 Without Guard")
    if st.button("Run Unguarded"):
        result = complete(
            model="claude-opus-4-8",
            prompt=[
                {"role": "system", "content": "You are a Revenue Ops assistant."},
                {"role": "user", "content": user_input}
            ],
            session=session,
            options=CompleteOptions(
                max_tokens=1024,
                temperature=0.3,
                guardrails=False  # No safety net
            )
        )
        st.write(result)

with col2:
    st.subheader("🛡️ With Cortex Guard")
    if st.button("Run Guarded"):
        result = complete(
            model="claude-opus-4-8",
            prompt=[
                {"role": "system", "content": "You are a Revenue Ops assistant."},
                {"role": "user", "content": user_input}
            ],
            session=session,
            options=CompleteOptions(
                max_tokens=1024,
                temperature=0.3,
                guardrails=True  # Llama Guard 3 evaluates output
            )
        )
        # Check for blocked response
        if "Response filtered by Cortex Guard" in str(result):
            st.error("⛔ Response BLOCKED by Cortex Guard")
            st.json(result)
        else:
            st.success("✅ Response passed Cortex Guard")
            st.write(result)

# ============================================================
# 2. Batch cost estimator
# ============================================================
st.divider()
st.subheader("💰 Guard Cost Estimator")

row_count = st.number_input("Estimated rows to process:", value=100000)
avg_tokens = st.number_input("Avg tokens per response:", value=500)

total_guard_tokens = row_count * avg_tokens
guard_credits = (total_guard_tokens / 1_000_000) * 0.05

st.metric("Total Guard Tokens", f"{total_guard_tokens:,.0f}")
st.metric("Estimated Guard Credits", f"{guard_credits:,.2f}")
st.caption("At $0.05 per million tokens — Cortex Guard is genuinely cheap")

# ============================================================
# 3. Production pattern: TRY_COMPLETE + Guard + Structured
# ============================================================
st.divider()
st.subheader("🏭 Production Pattern")
st.code("""
-- The complete production-grade AI pipeline:
-- 1. TRY_COMPLETE → fault tolerance (returns NULL on error)
-- 2. guardrails: true → content safety (Llama Guard 3)
-- 3. Structured output → Pydantic-style JSON
-- 4. AI_COUNT_TOKENS → cost forecasting
-- 5. RBAC → access control
-- 6. Budget controls → financial guardrails

SELECT SNOWFLAKE.CORTEX.TRY_COMPLETE(
    'claude-opus-4-8',
    [
        {'role': 'system', 'content': 'Return JSON: {sentiment, score, summary}'},
        {'role': 'user', 'content': f.FEEDBACK_TEXT}
    ],
    {'guardrails': true, 'temperature': 0.1}
) AS safe_structured_output
FROM REVENUE_OPS_AI.RAW.CUSTOMER_FEEDBACK f;
""", language="sql")
