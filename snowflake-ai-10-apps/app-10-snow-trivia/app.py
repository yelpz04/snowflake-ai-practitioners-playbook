# SnowTrivia — AI-Powered Quiz Game
# App 10 of 10: AI_COMPLETE (generation + validation) + Cortex Search + Streamlit

import streamlit as st
import json
import time
from snowflake.snowpark.context import get_active_session
from snowflake.cortex import Complete, CortexSearch

session = get_active_session()
st.set_page_config(page_title="SnowTrivia", page_icon="❄️", layout="centered")
st.title("❄️ SnowTrivia — AI-Powered Quiz Game")
st.caption("Questions generated from your documentation, grounded in real knowledge")

# ── Session state ─────────────────────────────────────────────────────────────
for key, default in [
    ("game_active", False), ("current_q", None), ("score", 0),
    ("q_count", 0), ("streak", 0), ("max_streak", 0),
    ("session_id", None), ("answered", False), ("player_name", ""),
    ("topic", ""), ("difficulty", "beginner"), ("feedback", None)
]:
    if key not in st.session_state:
        st.session_state[key] = default

DIFFICULTIES = ["beginner", "intermediate", "expert"]
TOPICS = ["Snowflake Architecture", "Cortex AI", "Zero-Copy Clone", "Data Sharing", "Time Travel", "SQL", "Data Engineering"]

def next_difficulty(score_pct: float, streak: int) -> str:
    if streak >= 3 and score_pct >= 70:
        return "expert"
    if streak >= 2 or score_pct >= 50:
        return "intermediate"
    return "beginner"

def generate_question(topic: str, difficulty: str) -> dict | None:
    # Retrieve relevant context from knowledge base
    results = CortexSearch.search(
        service="SNOW_TRIVIA.PUBLIC.KNOWLEDGE_SEARCH",
        query=topic, columns=["CONTENT", "TOPIC"], limit=2
    )
    context = "\n".join([r["CONTENT"] for r in (results.results if results else [])]) or topic

    raw = Complete(
        "claude-sonnet-4-5",
        f"""Create a {difficulty}-level multiple-choice quiz question about: {topic}
Based on this knowledge:
{context[:800]}

Return ONLY valid JSON (no markdown, no extra text):
{{
  "question": "...",
  "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
  "correct": "A",
  "explanation": "2-sentence explanation of why the answer is correct and what the others got wrong."
}}"""
    )
    try:
        # Strip markdown code fences if present
        clean = raw.strip()
        if clean.startswith("```"):
            clean = "\n".join(clean.split("\n")[1:-1])
        return json.loads(clean)
    except Exception:
        return None

# ── START SCREEN ─────────────────────────────────────────────────────────────
if not st.session_state.game_active:
    st.subheader("Start a new game")
    st.session_state.player_name = st.text_input("Your name:", value=st.session_state.player_name)
    st.session_state.topic       = st.selectbox("Topic:", TOPICS)
    num_questions = st.selectbox("Number of questions:", [5, 10, 15], index=0)

    if st.button("🚀 Start Game", type="primary", disabled=not st.session_state.player_name):
        result = session.sql(f"""
            INSERT INTO SNOW_TRIVIA.PUBLIC.GAME_SESSIONS (PLAYER_NAME, TOPIC)
            VALUES ('{st.session_state.player_name}', '{st.session_state.topic}')
        """).collect()
        sid = session.sql(
            f"SELECT SESSION_ID FROM SNOW_TRIVIA.PUBLIC.GAME_SESSIONS "
            f"WHERE PLAYER_NAME = '{st.session_state.player_name}' ORDER BY STARTED_AT DESC LIMIT 1"
        ).collect()[0][0]
        st.session_state.session_id   = sid
        st.session_state.game_active  = True
        st.session_state.score        = 0
        st.session_state.q_count      = 0
        st.session_state.streak       = 0
        st.session_state.max_streak   = 0
        st.session_state.total_q      = num_questions
        st.session_state.current_q    = None
        st.session_state.answered     = False
        st.session_state.feedback     = None
        st.rerun()

    # Leaderboard
    st.divider()
    st.subheader("🏆 Leaderboard")
    lb = session.sql("""
        SELECT PLAYER_NAME, TOPIC, BEST_SCORE, ROUND(BEST_PCT,1) AS best_pct, GAMES_PLAYED
        FROM SNOW_TRIVIA.PUBLIC.LEADERBOARD ORDER BY BEST_PCT DESC LIMIT 10
    """).to_pandas()
    if lb.empty:
        st.caption("No games played yet. Be the first!")
    else:
        st.dataframe(lb, use_container_width=True)

# ── GAME SCREEN ───────────────────────────────────────────────────────────────
else:
    total_q = st.session_state.get("total_q", 5)

    # Progress bar
    progress = st.session_state.q_count / total_q
    st.progress(progress, text=f"Question {st.session_state.q_count + 1} of {total_q}")

    col1, col2, col3 = st.columns(3)
    col1.metric("Score", st.session_state.score)
    col2.metric("Streak 🔥", st.session_state.streak)
    col3.metric("Difficulty", st.session_state.difficulty.capitalize())

    # Game over
    if st.session_state.q_count >= total_q:
        pct = st.session_state.score / total_q * 100
        st.balloons()
        st.success(f"🎉 Game over! {st.session_state.player_name} scored {st.session_state.score}/{total_q} ({pct:.0f}%)")
        st.metric("Max Streak", st.session_state.max_streak)

        session.sql(f"""
            UPDATE SNOW_TRIVIA.PUBLIC.GAME_SESSIONS
            SET SCORE={st.session_state.score}, TOTAL_QUESTIONS={total_q},
                MAX_STREAK={st.session_state.max_streak}, ENDED_AT=CURRENT_TIMESTAMP()
            WHERE SESSION_ID='{st.session_state.session_id}'
        """).collect()
        session.sql(f"""
            MERGE INTO SNOW_TRIVIA.PUBLIC.LEADERBOARD AS t
            USING (SELECT '{st.session_state.player_name}' AS p, '{st.session_state.topic}' AS tp,
                          {st.session_state.score} AS s, {pct} AS pct) AS src
            ON t.PLAYER_NAME = src.p AND t.TOPIC = src.tp
            WHEN MATCHED THEN UPDATE SET
                BEST_SCORE = GREATEST(t.BEST_SCORE, src.s),
                BEST_PCT   = GREATEST(t.BEST_PCT, src.pct),
                GAMES_PLAYED = t.GAMES_PLAYED + 1, LAST_PLAYED = CURRENT_TIMESTAMP()
            WHEN NOT MATCHED THEN INSERT (PLAYER_NAME, TOPIC, BEST_SCORE, BEST_PCT, GAMES_PLAYED)
                VALUES (src.p, src.tp, src.s, src.pct, 1)
        """).collect()

        if st.button("🔄 Play Again"):
            st.session_state.game_active = False
            st.rerun()
    else:
        # Generate new question if needed
        if st.session_state.current_q is None and not st.session_state.answered:
            score_pct = (st.session_state.score / max(st.session_state.q_count, 1)) * 100 if st.session_state.q_count > 0 else 50
            st.session_state.difficulty = next_difficulty(score_pct, st.session_state.streak)
            with st.spinner("AI is generating your next question..."):
                q = generate_question(st.session_state.topic, st.session_state.difficulty)
            st.session_state.current_q = q
            st.session_state.answered = False
            st.session_state.feedback = None

        q = st.session_state.current_q
        if q is None:
            st.error("Could not generate a question. Please check your Cortex Search service.")
        else:
            st.subheader(f"Q{st.session_state.q_count + 1}: {q['question']}")
            opts = q.get("options", {})
            choice = st.radio("Your answer:", list(opts.keys()),
                              format_func=lambda k: f"{k}. {opts[k]}",
                              disabled=st.session_state.answered,
                              key=f"q_{st.session_state.q_count}")

            if not st.session_state.answered:
                if st.button("Submit Answer", type="primary"):
                    correct = q.get("correct", "A")
                    is_correct = choice == correct
                    if is_correct:
                        st.session_state.score  += 1
                        st.session_state.streak += 1
                        st.session_state.max_streak = max(st.session_state.max_streak, st.session_state.streak)
                    else:
                        st.session_state.streak = 0
                    st.session_state.answered = True
                    st.session_state.feedback = (is_correct, correct, q.get("explanation", ""))
                    st.rerun()
            else:
                is_correct, correct, explanation = st.session_state.feedback
                if is_correct:
                    st.success(f"✅ Correct! {'+1 🔥' if st.session_state.streak > 1 else ''}")
                else:
                    st.error(f"❌ Wrong. The correct answer was **{correct}. {opts.get(correct, '')}**")
                st.info(f"**Explanation:** {explanation}")

                if st.button("➡️ Next Question"):
                    st.session_state.q_count  += 1
                    st.session_state.current_q = None
                    st.session_state.answered  = False
                    st.session_state.feedback  = None
                    st.rerun()
