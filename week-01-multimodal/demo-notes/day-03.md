# Day 3: Cortex AI Multimodal — Audio Sentiment Analysis

## Goal
Analyze a customer support call recording for sentiment, escalation signals, and actionable insights.

## References
- [Audio sentiment](https://docs.snowflake.com/en/user-guide/snowflake-cortex/ai-multimodal#audio-based-sentiment-analytics)

## What to Do
1. Upload a `.wav` or `.mp3` call recording to `@MEDIA_FILES_STAGE/audio/`
2. Run the Day 3 section of `03_multimodal_ai_queries.sql`
3. Insert results into `CALL_AI_INSIGHTS` table
4. Review sentiment, escalation, and follow-up recommendations

## Key Concepts
- Audio multimodal support is **Public Preview**
- AI_COMPLETE can detect tone, emotion, escalation signals from audio
- Output as JSON → parse into a structured insights table
- Useful for: support QA, compliance, customer health scoring

## Gotchas
- Audio file format support — check latest docs (WAV confirmed)
- File size limits for audio (longer recordings may need chunking)
- Model availability may vary by region

## LinkedIn Post Angle
"Your data warehouse can now listen. I analyzed a support call recording directly in Snowflake — no transcription pipeline, no third-party API."

## Medium Article Section
"Day 3: Audio intelligence in the warehouse — when Snowflake listens to your customer calls."

## Screenshot Checklist
- [ ] AI_COMPLETE query with audio input
- [ ] CALL_AI_INSIGHTS row showing sentiment, emotion, escalation
