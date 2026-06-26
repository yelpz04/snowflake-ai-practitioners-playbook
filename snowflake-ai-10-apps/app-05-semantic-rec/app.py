# SemanticRec — Arctic Embed Vector Recommendations
# App 5 of 10: EMBED_TEXT_768 + VECTOR_INNER_PRODUCT + Cortex Search

import streamlit as st
import pandas as pd
from snowflake.snowpark.context import get_active_session
from snowflake.cortex import CortexSearch

session = get_active_session()
st.set_page_config(page_title="SemanticRec", page_icon="🔮", layout="wide")
st.title("🔮 SemanticRec — Semantic Content Recommendations")
st.caption("Arctic Embed (EMBED_TEXT_768) + VECTOR_INNER_PRODUCT — no Python ML libraries needed")

tab1, tab2, tab3 = st.tabs(["🎯 Recommendations", "🔍 Semantic Search", "📊 Embedding Explorer"])

# ── TAB 1: Recommendations ───────────────────────────────────────────────────
with tab1:
    col1, col2 = st.columns([2, 1])
    with col2:
        sim_weight   = st.slider("Semantic weight", 0.0, 1.0, 0.7, 0.1)
        pop_weight   = round(1.0 - sim_weight, 1)
        top_n        = st.selectbox("Results to show:", [5, 10, 20], index=0)
        st.caption(f"Hybrid: {sim_weight*100:.0f}% semantic + {pop_weight*100:.0f}% popularity")

    content_list = session.sql(
        "SELECT CONTENT_ID, TITLE, CATEGORY FROM SEMANTICREC.PUBLIC.CONTENT ORDER BY VIEW_COUNT DESC LIMIT 50"
    ).to_pandas()

    if content_list.empty:
        st.info("No content found. Run setup.sql to seed sample data.")
    else:
        options = {f"{r['TITLE']} ({r['CATEGORY']})": r['CONTENT_ID']
                   for _, r in content_list.iterrows()}
        selected_label = st.selectbox("I liked this article — show me similar:", list(options.keys()))
        selected_id    = options[selected_label]

        if st.button("🔮 Find Similar Content"):
            with st.spinner("Computing semantic similarity..."):
                recs = session.sql(f"""
                    WITH target AS (
                        SELECT CONTENT_VECTOR FROM SEMANTICREC.PUBLIC.CONTENT
                        WHERE CONTENT_ID = '{selected_id}'
                    )
                    SELECT
                        c.CONTENT_ID, c.TITLE, c.CATEGORY, c.AUTHOR,
                        ROUND(VECTOR_INNER_PRODUCT(c.CONTENT_VECTOR, t.CONTENT_VECTOR) * 100, 1) AS semantic_pct,
                        c.VIEW_COUNT,
                        ROUND(
                            ({sim_weight} * VECTOR_INNER_PRODUCT(c.CONTENT_VECTOR, t.CONTENT_VECTOR))
                          + ({pop_weight} * LOG(1 + c.VIEW_COUNT) / NULLIF(LOG(1 + MAX(c.VIEW_COUNT) OVER()), 0))
                        , 4) AS hybrid_score
                    FROM SEMANTICREC.PUBLIC.CONTENT c, target t
                    WHERE c.CONTENT_ID != '{selected_id}'
                      AND c.CONTENT_VECTOR IS NOT NULL
                    ORDER BY hybrid_score DESC
                    LIMIT {top_n}
                """).to_pandas()

            if recs.empty:
                st.info("No recommendations. Ensure content has embeddings (run setup.sql UPDATE step).")
            else:
                st.subheader(f"Top {len(recs)} recommendations for: *{selected_label}*")
                for _, r in recs.iterrows():
                    with st.expander(f"**{r['TITLE']}** — {r['SEMANTIC_PCT']}% similar"):
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Semantic similarity", f"{r['SEMANTIC_PCT']}%")
                        c2.metric("Views", f"{r['VIEW_COUNT']:,}")
                        c3.metric("Hybrid score", f"{r['HYBRID_SCORE']:.4f}")
                        st.caption(f"Category: {r['CATEGORY']} | Author: {r['AUTHOR']}")

# ── TAB 2: Semantic Search ───────────────────────────────────────────────────
with tab2:
    search_q = st.text_input("Search by meaning:", placeholder="articles about real-time data pipelines")
    if search_q:
        results = CortexSearch.search(
            service="SEMANTICREC.PUBLIC.CONTENT_SEARCH",
            query=search_q,
            columns=["TITLE", "CATEGORY", "AUTHOR", "CONTENT_ID"],
            limit=10
        )
        for r in (results.results if results else []):
            st.write(f"**{r['TITLE']}** — {r['CATEGORY']}")

# ── TAB 3: Embedding Explorer ────────────────────────────────────────────────
with tab3:
    st.subheader("Compare two articles semantically")
    c1, c2 = st.columns(2)
    with c1:
        a = st.text_area("Article A (paste text):", height=100)
    with c2:
        b = st.text_area("Article B (paste text):", height=100)

    if a and b and st.button("Compute similarity"):
        with st.spinner("Embedding via Arctic Embed..."):
            result = session.sql(f"""
                SELECT ROUND(VECTOR_INNER_PRODUCT(
                    SNOWFLAKE.CORTEX.EMBED_TEXT_768('snowflake-arctic-embed-m', '{a.replace("'", "''")}'),
                    SNOWFLAKE.CORTEX.EMBED_TEXT_768('snowflake-arctic-embed-m', '{b.replace("'", "''")}')
                ) * 100, 2) AS similarity_pct
            """).collect()[0][0]
        st.metric("Cosine Similarity", f"{result}%")
        if result >= 80:
            st.success("Very similar — likely the same topic or near-duplicate.")
        elif result >= 50:
            st.info("Moderately related — overlapping concepts.")
        else:
            st.warning("Quite different — distinct topics.")
