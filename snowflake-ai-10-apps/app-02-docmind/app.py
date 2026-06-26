# DocMind — Enterprise Document Q&A
# App 2 of 10: Cortex Search + Multimodal AI

import streamlit as st
import json
from snowflake.snowpark.context import get_active_session
from snowflake.cortex import Complete, CortexSearch

session = get_active_session()

st.set_page_config(page_title="DocMind", page_icon="📄", layout="wide")
st.title("📄 DocMind — Ask Your Documents")
st.caption("Cortex Search + AI_COMPLETE — semantic search with AI-synthesised answers")

tab1, tab2, tab3 = st.tabs(["💬 Ask", "📁 Upload & Index", "📊 Usage"])

# ── TAB 1: Q&A ──────────────────────────────────────────────────────────────
with tab1:
    question = st.text_input("Ask a question across all your documents:")
    source_filter = st.selectbox("Filter by document type:", ["All", "pdf", "docx", "txt"])

    if question:
        with st.spinner("Searching documents..."):
            # Cortex Search: retrieve top-5 relevant chunks
            filters = {} if source_filter == "All" else {"@eq": {"SOURCE_TYPE": source_filter.lower()}}
            results = CortexSearch.search(
                service="DOCMIND.PUBLIC.DOCMIND_SEARCH",
                query=question,
                columns=["CHUNK_TEXT", "DOCUMENT_NAME", "CHUNK_INDEX"],
                filter=filters if filters else None,
                limit=5
            )

            chunks = results.results if results else []

            if not chunks:
                st.warning("No relevant documents found. Try uploading documents in the Upload tab.")
            else:
                # Build context for AI synthesis
                context = "\n\n".join([
                    f"[{c['DOCUMENT_NAME']} chunk {c['CHUNK_INDEX']}]: {c['CHUNK_TEXT'][:500]}"
                    for c in chunks
                ])

                answer = Complete(
                    "claude-sonnet-4-5",
                    f"""You are an enterprise knowledge assistant. Answer the question using ONLY the provided document excerpts.
If the answer is not in the documents, say "I couldn't find this in the available documents."
Always cite which document(s) you drew from.

Question: {question}

Document excerpts:
{context}

Answer:"""
                )

                st.markdown("### Answer")
                st.write(answer)

                st.markdown("### Sources")
                for c in chunks:
                    with st.expander(f"📄 {c['DOCUMENT_NAME']} — chunk {c['CHUNK_INDEX']}"):
                        st.write(c["CHUNK_TEXT"][:400] + "...")

                # Save to history
                session.sql("""
                    INSERT INTO DOCMIND.PUBLIC.QA_HISTORY (QUESTION, ANSWER, SOURCES_USED)
                    VALUES (?, ?, PARSE_JSON(?))
                """, params=[question, answer, json.dumps([c["DOCUMENT_NAME"] for c in chunks])]).collect()

# ── TAB 2: Upload & Index ────────────────────────────────────────────────────
with tab2:
    st.subheader("Document Inventory")
    st.info("Upload documents via: PUT file:///path/to/doc.pdf @DOCMIND.PUBLIC.DOCMIND_STAGE/ AUTO_COMPRESS=FALSE")

    docs = session.sql("""
        SELECT DOCUMENT_NAME, COUNT(*) AS chunks, MAX(CREATED_AT) AS indexed_at
        FROM DOCMIND.PUBLIC.DOCUMENT_CHUNKS
        GROUP BY DOCUMENT_NAME ORDER BY indexed_at DESC
    """).to_pandas()

    if docs.empty:
        st.warning("No documents indexed yet. Upload files to the DOCMIND_STAGE and run the ingestion SQL.")
    else:
        st.metric("Documents indexed", len(docs))
        st.dataframe(docs, use_container_width=True)

    if st.button("🔄 Index new documents from stage"):
        with st.spinner("Extracting text from new documents..."):
            session.sql("""
                INSERT INTO DOCMIND.PUBLIC.DOCUMENT_CHUNKS (DOCUMENT_NAME, CHUNK_INDEX, CHUNK_TEXT, SOURCE_TYPE)
                SELECT
                    RELATIVE_PATH,
                    ROW_NUMBER() OVER (PARTITION BY RELATIVE_PATH ORDER BY SEQ4()),
                    SNOWFLAKE.CORTEX.AI_COMPLETE(
                        'claude-sonnet-4-5',
                        'Extract the full text from this document. Return only raw text.',
                        {'media': [{'type': 'document', 'source': {
                            'type': 'stage',
                            'stage': '@DOCMIND.PUBLIC.DOCMIND_STAGE',
                            'path': RELATIVE_PATH
                        }}]}
                    ),
                    SPLIT_PART(RELATIVE_PATH, '.', -1)
                FROM DIRECTORY(@DOCMIND.PUBLIC.DOCMIND_STAGE)
                WHERE RELATIVE_PATH NOT IN (SELECT DISTINCT DOCUMENT_NAME FROM DOCMIND.PUBLIC.DOCUMENT_CHUNKS)
            """).collect()
            st.success("Indexing complete. Cortex Search will update within 1 hour.")

# ── TAB 3: Usage ─────────────────────────────────────────────────────────────
with tab3:
    st.subheader("Q&A History")
    history = session.sql("""
        SELECT QUESTION, LEFT(ANSWER, 100) || '...' AS answer_preview,
               ASKED_AT FROM DOCMIND.PUBLIC.QA_HISTORY
        ORDER BY ASKED_AT DESC LIMIT 20
    """).to_pandas()
    st.dataframe(history, use_container_width=True)
