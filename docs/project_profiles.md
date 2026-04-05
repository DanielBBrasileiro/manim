## Project Profiles

Project profiles are a lightweight production-defaults layer.

Resolution order:
1. explicit briefing / plan override
2. reference-native direction
3. project profile defaults
4. style-pack or global fallback

What project profiles do:
- provide valid default targets
- set a default style direction for recurring production contexts
- reduce operator repetition when using `python3 aiox.py create ... --project <project_id>`

What project profiles do not do:
- they do not override explicit briefing choices
- they do not override reference-native direction
- they do not define output directory routing
- they do not provide target-specific nested override logic

Current profiles:
- `linkedin_tecnico`
- `reels_instagram_premium`
- `reels_instagram_minimalista`
