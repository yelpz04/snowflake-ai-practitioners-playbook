# Day 2: Cortex AI Multimodal — Document/Image Extraction

## Goal
Use `AI_COMPLETE` with image files on a Snowflake stage to extract structured data.

## References
- [Multimodal docs](https://docs.snowflake.com/en/user-guide/snowflake-cortex/ai-multimodal)

## What to Do
1. Upload sample invoice/product images to `@MEDIA_FILES_STAGE/images/`
2. Run `02_create_media_stage.sql` to create the stage and tracking table
3. Run the Day 2 section of `03_multimodal_ai_queries.sql`
4. Verify AI output in `MEDIA_AI_RESULTS`

## Key Concepts
- `AI_COMPLETE` accepts a `media` array with `type: 'image'` and stage source
- Output is unstructured text — parse it into VARIANT for downstream use
- Supported models: claude-3-5-sonnet (check latest docs for updates)
- **Public Preview**: audio and video support

## Gotchas
- Files must be on a Snowflake stage, not external URLs
- Image file size limits apply — check docs for current limits
- AUTO_COMPRESS=FALSE when uploading media files via PUT
