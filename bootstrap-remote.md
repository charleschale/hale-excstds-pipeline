# First-time setup: local git + push to GitHub

The pipeline files are all written and ready. `git init` from my sandbox hit a OneDrive file-lock permission issue and left a partial `.git/` folder that needs to be cleaned up. Run the commands below from your local terminal (Windows PowerShell, macOS/Linux shell, or WSL) and you'll be in a clean state in under a minute.

## Step 1 — Clean up the partial `.git/` folder and re-init locally

From `C:\Users\charl\OneDrive\old\Documents\Claude\Projects\Exc Stds\_pipeline\` (PowerShell):

```powershell
Remove-Item -Recurse -Force .git
git init -b main
git add -A
git commit -m "Initial commit: ExcStds + TTI pipeline skeleton"
```

Or (WSL / macOS / Linux shell):

```bash
rm -rf .git
git init -b main
git add -A
git commit -m "Initial commit: ExcStds + TTI pipeline skeleton"
```

If OneDrive blocks the `Remove-Item`, pause OneDrive sync from the tray icon, run the commands, then resume sync.

## Step 2 — Push to GitHub

### Option A — `gh` CLI (fastest, one command)

```bash
gh repo create hale-excstds-pipeline --private --source=. --remote=origin --push
```

Creates the GitHub repo, adds it as `origin`, pushes `main`. Done.

### Option B — GitHub web UI

1. Create the repo on https://github.com/new. Name: `hale-excstds-pipeline`. Private. Do **not** initialize with README, .gitignore, or license — the local repo already has those.
2. Copy the repo URL shown on the next page.
3. In your terminal:

   ```bash
   git remote add origin <repo-url>
   git push -u origin main
   ```

## Step 3 — Connect Render

1. Render dashboard → New → Web Service → connect GitHub if not already → pick `hale-excstds-pipeline`.
2. Render auto-detects `render.yaml` and pre-fills build / start commands.
3. Set the env vars listed as `sync: false` in `render.yaml`:
   - `PBI_TENANT_ID`, `PBI_CLIENT_ID`, `PBI_CLIENT_SECRET`
   - `PBI_WORKSPACE_ID`, `PBI_DATASET_ID`
   - `EXCSTDS_EXPORT_TOKEN`
   - `PIPELINE_API_TOKEN` (invent any long random string — clients will use this as their bearer token)
4. Deploy. First build ~3 minutes. Test `https://<your-service>.onrender.com/healthz` returns `{"status":"ok"}`.

## Step 4 — Configure your local `.env`

From the pipeline folder:

```bash
cp .env.example .env
# Edit .env and fill in:
#   PIPELINE_URL         = your Render URL (e.g. https://hale-excstds-pipeline.onrender.com)
#   PIPELINE_API_TOKEN   = same value you set on Render in Step 3
#   LOCAL_RESPONDENT_ROOT = absolute path to where respondent folders should be created
#                           (e.g. C:/Users/charl/OneDrive/old/Documents/Claude/Projects/Exc Stds)
```

If you want to test the pipeline end-to-end locally *without* Render, also fill in all the PBI_* and EXCSTDS_EXPORT_* vars — `scripts/run_local.py` uses those.

## Step 5 — First real run

Against Render:

```bash
python scripts/pull_local.py 20260414.mnm.riggs@gmail.com
```

Locally (no Render, requires all secrets in .env):

```bash
python scripts/run_local.py 20260414.mnm.riggs@gmail.com
```

Either command should produce `<LOCAL_RESPONDENT_ROOT>/20260414.mnm.riggs@gmail.com/data.xlsx` with 8 populated tabs matching the structure of the Meriste build's `Book1.xlsx`.

## Ongoing updates

```bash
git add -A
git commit -m "your message"
git push
```

Render auto-deploys from `main`.
