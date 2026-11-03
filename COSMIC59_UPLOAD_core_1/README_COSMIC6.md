# COSMIC 6.0 upgrade branch

This is an incremental upgrade branch based on the existing COSMIC 5.9 source. The default branch is not changed.

## Deployment
The Dockerfile in this branch installs pinned calculation dependencies from `requirements-v6.txt`.
Deploy this branch's `COSMIC59_UPLOAD_core_1` directory using the existing Render/Docker deployment settings. Preserve existing environment variables, especially `OPENAI_API_KEY` and `COSMIC_AI_ACCESS_CODE`; do not commit secrets.

After deployment:
- Existing homepage: `/`
- Interactive COSMIC 6.0 UI: `/cosmic6-app.html`
- UI/report preview: `/cosmic6-preview.html`
- Health: `/health`

## API
- `POST /api/v2/cosmic/analyze` — legacy BaZi engine + iztro-py Zi Wei chart + lunar calendar.
- `POST /api/v2/cosmic/yijing/cast` — six-coin toss result with moving lines and trigrams.
- `POST /api/v2/cosmic/lingqian/draw` — random 1–100 lot number. Full text interpretation is intentionally withheld until a source-verified Huangdaxian 100-lot dataset is installed.
- `POST /api/v2/cosmic/fengshui/flying-stars` — annual flying-star base chart. This is not a complete natal house chart.

## Important scope and accuracy notes
This branch adds callable modules and a UI, but it is not honest to label every requested metaphysics module as complete yet:
1. Zi Wei uses the external `iztro-py` calculation library; its returned chart is passed through as structured output. Verify the selected school/rule options against the desired product conventions before production interpretation.
2. BaZi remains the existing engine. Its year/month/day/hour and annual logic have not been fully audited against independent ephemeris test vectors in this change.
3. Yijing currently computes a six-line coin-cast record and trigrams. It does not yet include a verified 64-hexagram text corpus, line-text citation, or school-specific interpretive rules.
4. Huangdaxian currently draws a number only. The 100-lot text corpus needs a selected, source-verified edition; the schema is in `data/huangdaxian_100.schema.json`. No invented lot poem or explanation is returned.
5. Fengshui currently returns a basic annual flying-star layout. Full Xuan Kong house chart, mountain/water stars, facing/sitting boundaries and period transitions need precise compass data, build/major-renovation date, floor plan and chosen school.
6. Daily 12-hour and monthly detailed fortunes, health/food/clothing advice, and jewelry recipes must be tied to the verified chart evidence; no fixed generic fortunes should be presented as calculated results.

## Validation
Run `python -m compileall -q .` in the application directory after dependency installation. Then smoke-test all endpoints above with a real birth payload. Never overwrite the production default branch until tests pass.
