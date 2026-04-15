# hale-excstds-pipeline

Respondent data pull for Hale Global's Excellence Standards + TTI coaching workflow. Given a Key3, fetches scored measures from Power BI and non-scorable text answers from `haleglobal.com/excellence_export.php`, assembles them into a single xlsx workbook, and returns it over HTTP.

This service is the automation of what was previously a manual DAX Studio workflow (documented in `../dax_queries.md` in the parent project).

## Architecture

Three data sources, one output:

- **Power BI `executeQueries` REST API** — scored measures (L1/L2/Flags/Skinny/Impact Top-10/Teach Top-10). The scoring algorithm lives in the Power BI DAX measures; we don't reimplement it.
- **`excellence_export.php?table=text`** — non-scorable text answers (Q76, Q104-114, Q9911+ series).
- **`excellence_export.php?table=Lkup_Key`** — respondent metadata and Key3 validation.

Output is one xlsx with the tabs `L1`, `L2`, `Flags`, `Skinny`, `ImpactTop10`, `TeachTop10`, `Non-Scorable`, `Metadata`.

## Running locally

### First-time setup

```bash
python -m venv .venv
source .venv/bin/activate       # macOS/Linux
# or
.venv\Scripts\activate          # Windows

pip install -r requirements.txt
cp .env.example .env
# Fill in the secret values in .env — see comments inside.
```

### Run the pipeline directly (no Render)

```bash
python scripts/run_local.py 20260414.mnm.riggs@gmail.com
```

Writes `{LOCAL_RESPONDENT_ROOT}/20260414.mnm.riggs@gmail.com/data.xlsx`.

### Run against a deployed Render service (thin client)

```bash
python scripts/pull_local.py 20260414.mnm.riggs@gmail.com
```

Same output path, but hits the Render service over HTTP. The local client only needs `PIPELINE_URL` and `PIPELINE_API_TOKEN` — no Power BI or MySQL secrets.

### Run the FastAPI server locally (for development)

```bash
uvicorn src.server.app:app --reload --port 8000
```

Then test:

```bash
curl -X POST http://localhost:8000/v1/pull-respondent \
  -H "Authorization: Bearer $PIPELINE_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"key3":"20260414.mnm.riggs@gmail.com"}' \
  --output data.xlsx
```

## Deploying to Render

1. Push this repo to GitHub.
2. In Render, create a new Web Service pointing at the repo. The `render.yaml` in the root auto-configures the build and start commands.
3. Set the env vars marked `sync: false` in `render.yaml` via Render's dashboard:
   - `PBI_TENANT_ID`, `PBI_CLIENT_ID`, `PBI_CLIENT_SECRET`
   - `PBI_WORKSPACE_ID`, `PBI_DATASET_ID`
   - `EXCSTDS_EXPORT_TOKEN`
   - `PIPELINE_API_TOKEN` (any long random string — local clients present this as a bearer token)
4. Render will deploy on every push to the default branch.

## Endpoints

### `GET /healthz`

Liveness probe. Returns `{"status": "ok"}`.

### `POST /v1/pull-respondent`

Header: `Authorization: Bearer $PIPELINE_API_TOKEN`
Body: `{"key3": "<respondent-key3>"}`

Returns the xlsx file as binary (`Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`). 404 if the Key3 isn't found in `Lkup_Key`.

## DAX queries

DAX templates live in `dax/`. Each file contains a single query with `{KEY3}` as the placeholder. `src/pipeline/powerbi.py::render_query` substitutes the real Key3 before sending. Templates are mirrored from `../dax_queries.md` so the canonical form stays documented in the parent methodology project.

To add a query: drop a new `.dax` file in `dax/`, add a tuple to `POWERBI_QUERIES` in `src/pipeline/runner.py`, and redeploy.

## Secrets hygiene

- Secrets never live in code or in this repo. They go in `.env` locally (which is gitignored) and in Render's dashboard in production.
- The `excellence_export.php` token is passed as a URL query parameter because that's what the upstream endpoint requires. This is a known weakness of the upstream design; not fixing it here.
- Rotate the `PIPELINE_API_TOKEN` at any time by updating it on Render and in local `.env` files.

## Out of scope for v1

- Concurrent respondent pulls (current design handles one Key3 per request; concurrent clients work fine but there's no batching)
- Caching (every request hits Power BI fresh; add Redis/TTL if volume grows)
- MySQL direct connection (the PHP endpoint covers everything we need)
- TTI PDF parsing (still manual; a later pipeline stage)
- Draft report generation (still produced by Claude after data pull; a later pipeline stage)

## See also

- `../METHODOLOGY.md` — the coaching-guide and hiring-manager-report methodology this pipeline feeds
- `../dax_queries.md` — canonical DAX set with extensive documentation on pitfalls
