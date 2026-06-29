# DocMind — Enterprise Document Q&A using Cortex Search REST API + Complete via SQL

import os
import json
import requests
import streamlit as st

conn = st.connection("snowflake", ttl=os.getenv("SNOWFLAKE_CONNECTION_TTL"))
session = conn.session()

st.set_page_config(page_title="DocMind", page_icon="📄", layout="wide")
st.title("📄 DocMind : Ask Your Documents")
st.caption("Cortex Search + AI_COMPLETE = semantic search with AI-synthesised answers")


def cortex_search(question, source_filter, limit=5):
    """Query Cortex Search service via the Snowflake REST API."""
    sf_raw = conn._instance          # snowflake.connector.SnowflakeConnection
    host   = sf_raw.host             # e.g. qk69635.snowflakecomputing.com
    token  = sf_raw.rest.token       # current session token

    url = (
        f"https://{host}/api/v2/databases/DOCMIND/schemas/PUBLIC"
        "/cortex-search-services/DOCMIND_SEARCH:query"
    )
    headers = {
        "Authorization": f'Snowflake Token="{token}"',
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    body = {
        "query": question,
        "columns": ["CHUNK_TEXT", "DOCUMENT_NAME", "CHUNK_INDEX"],
        "limit": limit,
    }
    if source_filter != "All":
        body["filter"] = {"@eq": {"SOURCE_TYPE": source_filter.lower()}}

    resp = requests.post(url, headers=headers, json=body, timeout=30)
    resp.raise_for_status()
    return resp.json().get("results", [])


def cortex_complete(prompt):
    """Call COMPLETE via SQL — no Python SDK required."""
    row = session.sql(
        "SELECT SNOWFLAKE.CORTEX.COMPLETE(?, ?)",
        params=["claude-sonnet-4-5", prompt],
    ).collect()
    return row[0][0]


tab1, tab2, tab3 = st.tabs(["💬 Ask", "📁 Upload & Index", "📊 Usage"])

# ── TAB 1: Q&A ───────────────────────────────────────────────────────────────
with tab1:
    question      = st.text_input("Ask a question across all your documents:")
    source_filter = st.selectbox("Filter by document type:", ["All", "pdf", "docx", "txt"])

    if question:
        with st.spinner("Searching documents..."):
            chunks = cortex_search(question, source_filter)

            if not chunks:
                st.warning("No relevant documents found. Try uploading documents in the Upload tab.")
            else:
                context = "\n\n".join([
                    f"[{c['DOCUMENT_NAME']} chunk {c['CHUNK_INDEX']}]: {c['CHUNK_TEXT'][:500]}"
                    for c in chunks
                ])

                prompt = (
                    "You are an enterprise knowledge assistant. Answer the question using ONLY "
                    "the provided document excerpts.\n"
                    "If the answer is not in the documents, say \"I couldn't find this in the available documents.\"\n"
                    "Always cite which document(s) you drew from.\n\n"
                    f"Question: {question}\n\n"
                    f"Document excerpts:\n{context}\n\nAnswer:"
                )

                answer = cortex_complete(prompt)

                st.markdown("### Answer")
                st.write(answer)

                st.markdown("### Sources")
                for c in chunks:
                    with st.expander(f"📄 {c['DOCUMENT_NAME']} — chunk {c['CHUNK_INDEX']}"):
                        st.write(c["CHUNK_TEXT"][:400] + "...")

                try:
                    session.sql(
                        "INSERT INTO DOCMIND.PUBLIC.QA_HISTORY (QUESTION, ANSWER, SOURCES_USED)"
                        " VALUES (?, ?, PARSE_JSON(?))",
                        params=[question, answer, json.dumps([c["DOCUMENT_NAME"] for c in chunks])],
                    ).collect()
                except Exception:
                    pass  # history table may not exist yet; non-fatal

# ── TAB 2: Upload & Index ─────────────────────────────────────────────────────
with tab2:
    st.subheader("Document Inventory")
    st.info("Upload documents via: PUT file:///path/to/doc.pdf @DOCMIND.PUBLIC.DOCMIND_STAGE/ AUTO_COMPRESS=FALSE")

    try:
        docs = session.sql("""
            SELECT DOCUMENT_NAME, COUNT(*) AS chunks, MAX(CREATED_AT) AS indexed_at
            FROM DOCMIND.PUBLIC.DOCUMENT_CHUNKS
            GROUP BY DOCUMENT_NAME ORDER BY indexed_at DESC
        """).to_pandas()
    except Exception as e:
        st.error(f"Could not load document inventory: {e}")
        docs = None

    if docs is None:
        pass
    elif docs.empty:
        st.warning("No documents indexed yet. Upload files to the DOCMIND_STAGE and run the ingestion SQL.")
    else:
        st.metric("Documents indexed", len(docs))
        st.dataframe(docs, use_container_width=True)

    if st.button("🔄 Index new documents from stage"):
        with st.spinner("Extracting text from new documents..."):
            try:
                session.sql("""
                    INSERT INTO DOCMIND.PUBLIC.DOCUMENT_CHUNKS
                        (DOCUMENT_NAME, CHUNK_INDEX, CHUNK_TEXT, SOURCE_TYPE)
                    SELECT
                        RELATIVE_PATH,
                        1 AS CHUNK_INDEX,
                        SNOWFLAKE.CORTEX.AI_PARSE_DOCUMENT(
                            BUILD_SCOPED_FILE_URL(@DOCMIND.PUBLIC.DOCMIND_STAGE, RELATIVE_PATH),
                            OBJECT_CONSTRUCT('mode', 'LAYOUT')
                        ):text::STRING AS CHUNK_TEXT,
                        SPLIT_PART(RELATIVE_PATH, '.', -1) AS SOURCE_TYPE
                    FROM DIRECTORY(@DOCMIND.PUBLIC.DOCMIND_STAGE)
                    WHERE RELATIVE_PATH NOT IN (
                        SELECT DISTINCT DOCUMENT_NAME FROM DOCMIND.PUBLIC.DOCUMENT_CHUNKS
                    )
                """).collect()
                st.success("Indexing complete. Cortex Search will update within 1 hour.")
            except Exception as e:
                st.error(f"Indexing failed: {e}")

# ── TAB 3: Usage ──────────────────────────────────────────────────────────────
with tab3:
    st.subheader("Q&A History")
    try:
        history = session.sql("""
            SELECT QUESTION, LEFT(ANSWER, 100) || '...' AS answer_preview,
                   ASKED_AT FROM DOCMIND.PUBLIC.QA_HISTORY
            ORDER BY ASKED_AT DESC LIMIT 20
        """).to_pandas()
        st.dataframe(history, use_container_width=True)
    except Exception as e:
        st.error(f"Could not load Q&A history: {e}")
