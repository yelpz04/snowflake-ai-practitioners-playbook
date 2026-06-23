# Day 4: Cortex AI Multimodal — Video Metadata Extraction

## Goal
Extract structured content metadata from a product demo video using Cortex AI.

## References
- [Video extraction](https://docs.snowflake.com/en/user-guide/snowflake-cortex/ai-multimodal#video-metadata-extraction)
- [Multimodal blog](https://www.snowflake.com/en/blog/multimodal-analytics-ai-video-audio-images/)

## What to Do
1. Upload a short `.mp4` demo video to `@MEDIA_FILES_STAGE/video/`
2. Run the Day 4 section of `03_multimodal_ai_queries.sql`
3. Insert results into `VIDEO_AI_INSIGHTS`
4. Review content safety, marketing quality score, brand mentions

## Key Concepts
- Video multimodal support is **Public Preview**
- AI_COMPLETE extracts visual + audio + temporal signals from video
- Content safety checking built into the prompt
- Marketing/brand intelligence use case

## Real-World Use Cases
- **Brand monitoring**: detect unauthorized logo usage in partner videos
- **Content QA**: automated quality scoring before publishing
- **Compliance**: content safety checks at scale
- **Catalog enrichment**: auto-generate video descriptions and tags

## LinkedIn Post Angle
"I uploaded a product demo video to Snowflake and asked it: What products are shown? Is the content brand-safe? What audience is it for? All answered with one SQL query."

## Medium Article Section
"Day 4: Video intelligence meets the data warehouse — content analysis without leaving Snowflake."

## Screenshot Checklist
- [ ] AI_COMPLETE query with video input
- [ ] VIDEO_AI_INSIGHTS showing themes, tone, quality score
