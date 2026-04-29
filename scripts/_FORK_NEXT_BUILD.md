# Fork-Next-Build Checklist

When starting a new Excellence Standards report (hiring or coaching), do NOT
fork from the most recently shipped `build_<name>_*.py` — fork from the
`_template_*` files in this directory. They capture the latest state of the
qa_gate + print-CSS contract and import shared modules so future rule
changes propagate automatically.

## For a new coaching guide (Variant 1)

```
cp _pipeline/scripts/_template_coaching_build.py  _pipeline/scripts/build_<slug>_coaching.py
cp _pipeline/scripts/_template_coaching_render.js _pipeline/scripts/render_<slug>_coaching_pdf.js
```

Then in `build_<slug>_coaching.py`:
1. Edit `SLUG`, `CANDIDATE`, `CANDIDATE_FN`, `RESPONDENT_ID`, `REPORT_DATE`,
   `CANDIDATE_CREDS`, `CANDIDATE_ROLE` at the top.
2. Implement `load_respondent_data`, `load_histogram_data`,
   `build_distribution_tokens`, `build_respondent_dict`,
   `build_excstds_scorecard` by copying from a recent canonical build
   (`build_bender_coaching.py` is the most recent reference as of 2026-04-28).
3. Fill in the candidate-specific narrative blocks (Signature Pattern,
   Fingerprint, Driving Forces, etc.).
4. Build the >=22 cards (3+ flag-driven, 9+ per-answer impact, 10+ teach)
   using the canonical card structure documented in `build_impact_items_html`.
5. Run the script. The shared `qa_gate_coaching()` will fail the build if
   any of the S11g + S11h + structural-balance rules is violated.

In `render_<slug>_coaching_pdf.js`:
1. Edit `SLUG`, `CANDIDATE_NAME`, `PDF_VERSION` at the top.
2. The print-CSS contract is loaded automatically from `_print_css.json`.
3. The canvas health-check fails fast if Chart.js drops a buffer.

## For a new hiring report (Variant 2)

```
cp _pipeline/scripts/_template_hiring_build.py  _pipeline/scripts/build_<slug>_hiring.py
cp _pipeline/scripts/_template_hiring_render.js _pipeline/scripts/render_<slug>_pdf.js
```

Same pattern. Reference build: `build_houston_hiring.py` (most recent as of
2026-04-28).

## When a new rule gets codified during a build

The discipline that keeps the templates honest:

1. Land the rule prose in `METHODOLOGY.md`.
2. Land the per-section checklist item in `_pipeline/QA_CHECKLIST.md`.
3. Implement the check in `_pipeline/src/pipeline/qa_gate.py` (so it runs
   for all future builds via `qa_gate_coaching()` / `qa_gate_hiring()`).
4. If the rule affects the print-CSS contract, edit `_print_css.json`.
5. Optionally update the in-line guidance in the relevant `_template_*` file.

The shipped builds (`build_bender_coaching.py`, `build_houston_hiring.py`,
etc.) are NOT retroactively updated — they are frozen against the qa_gate
that existed at the time of shipping. Re-running an old build with a newer
qa_gate may now fail; that is expected and not a regression.

## File integrity discipline

The Edit tool + OneDrive sync occasionally truncate files mid-write. After
ANY edit to:
- `_template_*_build.py`
- `_template_*_render.js`
- `_print_css.json`
- `_pipeline/src/pipeline/qa_gate.py`
- `_templates/*.html`

verify file integrity:
- Python files: `python -c "import ast; ast.parse(open(\"<path>\").read())"`
- JS files:     `node --check <path>`
- JSON files:   `python -c "import json; json.load(open(\"<path>\"))"`
- HTML:         `tail -c 10 <path>` should end in `</html>` for templates

If truncated, restore the missing tail with `git show HEAD:<path>` before
proceeding.
