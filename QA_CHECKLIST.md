# Hiring-Report QA Checklist (Source of Truth)

This file is **the contract** that every hiring-report build MUST pass. Every item below
maps to an assertion that the build script runs post-render; if any fail, the build
must fail loudly (non-zero exit, error banner). This exists because structural drift
has been invisible to previous QA (token-fill + brand lockup passed while sections
were silently wrong). The canonical rendered reference is
`_reports/Bender_Jody_hiring_report.html` and the canonical structural template is
`_templates/hiring_report_TEMPLATE.html`. Cole and Harinam use the updated population
distribution variant (collapse-empty + reverse flag axis) — that is the CURRENT
standard Hechler and all new reports must follow.

Convention: `exact N` = count must equal N. `min N` = count must be >= N. `truthy` = boolean non-empty check.

## Section 1 — Targeted Concerns
- [ ] `class="concern-item"` — min 2 (count is data-driven; a respondent may surface 2, 3, or more concerns)
- [ ] `class="concern-number"` count equals `class="concern-item"` count (triplet parity)
- [ ] `class="concern-text"` count equals `class="concern-item"` count (triplet parity)
- [ ] Concern numbers render 1..N sequentially (no skips)
- [ ] Each `.concern-text` opens with `<strong>Title.</strong>` pattern (bold lead-in)

## Section 2 — Headline Metrics (narrow cells)
- [ ] `.metric-value` contains a **literal number or fraction** for:
  - Z|Algo Overall — signed decimal to 2 places (e.g., `+0.23`, `-0.87`)
  - Reverse Flags — integer count of RFs fired
  - Flags Lit — integer count of flags lit
  - Teach Items — fraction `N/10` (count of respondent's Top-10 teach items, from `TeachTop10` sheet)
  - Hard-to-Learn — fraction like `2 of 4` (count of failed gates)
- [ ] NO sentence / narrative text in any `.metric-value` cell
- [ ] `TEACH_ITEMS` token never contains the string "To be populated" or "Q47" or "Q81"

## Section 3 — Wiring-Fit Check
- [ ] `class="wiring-fit-content"` — exact 1
- [ ] `class="wiring-flag"` — exact 2 pills
- [ ] Exactly 2 `<strong>`-led items in the wiring-fit-content div
- [ ] Each item ties explicitly to one of the two Targeted Concerns

## Section 4 — Population Distribution Charts
All three canvases must exist and render (confirmed via Puppeteer canvas pixel check).

### Chart 1 (`distChart1`) — Z|Algo + Z|Human dual histogram
- [ ] Labels token `DIST_ZLABELS` is JSON array of 2-element string arrays (pre-split for 2-row axis): `[["-3.5","-3.0"],...]`
- [ ] Empty end bins ARE collapsed (leading/trailing zero columns hidden)
- [ ] `algoCounts` and `humanCounts` arrays have same length as labels
- [ ] Respondent markers `jAlgoBin` (triangle) and `jHumanBin` (diamond) map to post-collapse indices
- [ ] Y-axis left side (default position)

### Chart 2 (`distChart2`) — Success vs Fail cohorts
- [ ] Labels token `DIST_SF_LABELS` is JSON 2-row array
- [ ] **Empty columns (fail=0 AND success=0 in both) MUST be hidden** (critical requirement)
- [ ] Last visible label ends with `+` (outlier collapse into edge bin)
- [ ] `failData2` colored `#e74c3c` (red), `successData2` colored `#27ae60` (green)
- [ ] Legend visible (top position, font size 7)

### Chart 3 (`distChart3`) — Reverse Flag Counts
- [ ] Labels token `DIST_FLAG_LABELS` is JSON 2-row array for 5-unit bins (0-5 through 45-50+)
- [ ] **Axis order is REVERSED: high flags on LEFT, low flags on RIGHT** (right = better, matching z-score convention). This matches Cole/Harinam convention.
- [ ] Y-axis positioned on RIGHT (`position: 'right'`)
- [ ] Data sourced from Zalgo summ `@#RF` column (col 7), NOT from `Histogram Flags` bin-edge sheet
- [ ] Respondent marker at post-reverse bin index

## Section 5 — DISC Wiring Panel
- [ ] Canvas `discChart` present and renders
- [ ] `.disc-row` count matches TTI D/I/S/C natural + adapted (at least 8 rows)

## Section 6 — Excellence Standards Dimensional Scorecard
- [ ] Canvas `excstdsChart` present and renders
- [ ] `excLabels` is hierarchical: L1 rows in `UPPERCASE`, L2 rows indented with 4 leading spaces
- [ ] `isL1` boolean array matches `excLabels` length
- [ ] Each L1 row followed by 2–5 of its L2 sub-dimensions
- [ ] Minimum row count: 12 (reference Bender has 13). This confirms L2 sub-dimensions are rendering.
- [ ] L2 scores sourced from `L2` sheet `[Score5_filtered]` column (SKILL.md line 55 — canonical source)
- [ ] Context caption present mentioning "UPPERCASE = L1 category"
- [ ] Overall Z|Algo gold marker line and Cohort grey marker line both drawn

## Section 7 — Talent Attributes Radar
- [ ] Canvas `talentRadar` present
- [ ] Labels exactly `['Two-Sport Athlete', 'Punctuates Differently', 'Facilitative Mindset', 'Wit \u2298', 'Deep Repertoire', 'Discipline/Routine', 'Understands Symbolism \u2298']` (7 Bible attributes in this order)
- [ ] Data is 7-element array; positions 3 (Wit) and 6 (Symbolism) MUST be `null` (not assessable by survey)
- [ ] Other 5 positions contain integer 1-5 scores (or narrative-justified N/A)

## Section 8 — Career Timeline
- [ ] `class="timeline-block"` — min 4 (one per major employer)
- [ ] `class="timeline-legend"` — exact 1
- [ ] `class="legend-item"` — matches timeline-block count (each block has a legend row with color dot)
- [ ] `class="timeline-banner"` — exact 1 (tenure-pattern summary)
- [ ] Career data sourced from saved LinkedIn file `_pipeline/data/<slug>_linkedin.md` (NEVER inferred/invented — build must fail if LinkedIn data is missing)

## Section 9 — Interview Probes (CRITICAL: Form 8 sourcing)

**Form 8 sourcing is a non-negotiable contract.** Interview probes are drawn VERBATIM from the canonical Form 8 set defined in PROJECT_NOTES.md. They are NOT generated, NOT paraphrased, and NOT substituted. Freelanced probe questions are the failure mode the ExcStds methodology was built to replace. See PROJECT_NOTES.md `## Interview Questions (Form 8) — CRITICAL, NON-NEGOTIABLE` for the full rationale and exception policy.

### Structural checks

- [ ] `class="probe-card"` — exact 10
- [ ] `class="probe-number"` — exact 10
- [ ] `class="probe-category"` — exact 10
- [ ] `class="probe-question"` — exact 10
- [ ] `class="probe-coaching"` — exact 10

### Form 8 sourcing checks (enforced in `qa_gate()`)

- [ ] **All 10 canonical Form 8 questions must be present** in the rendered report. `qa_gate()` matches a distinctive substring from each Form 8 question against each `.probe-question` block; the build FAILS if fewer than 10 of 10 canonical questions are found.
- [ ] Probe questions are drawn verbatim from the Form 8 set (no paraphrasing, no substitution).
- [ ] Probe-question display text does NOT begin with `"Form 8 #N —"` label. The reader sees the canonical question in quotes as it will be asked in the interview.
- [ ] Each probe's **probe-category** label is tailored to the candidate (links the Form 8 question to a specific flag / concern / wiring signal).
- [ ] Each probe's **probe-coaching** note is tailored to the candidate's specific data patterns (career history, flag profile, wiring mismatches).
- [ ] Coaching notes do NOT begin with `"Listen for:"` prefix.

### Canonical Form 8 question set (source of truth: PROJECT_NOTES.md)

The build script mirrors these as `FORM8_QUESTIONS` with a distinctive substring per question used for QA matching.

1. **Two-Sport Athlete** — "Of all the things you've done in life, tell me what results you're most proud of." (match substring: `most proud of`)
2. **Talent Development** — "What people over your career have you nurtured who have gone on to do great things?" (match: `nurtured who have gone on`)
3. **TORC** — "What was your boss's name? What will they say your strengths and areas for improvement were?" (match: `strengths and areas for improvement`)
4. **Emotional Maturity** — "What's the greatest adversity you've faced in life?" (match: `greatest adversity`)
5. **Punctuates Differently** — "What do you do to achieve excellence that others don't?" (match: `achieve excellence that others don`)
6. **Facilitative Mindset** — "What's something you really believe in? When is it okay to make exceptions?" (match: `okay to make exceptions`)
7. **Commitment** — "Tell me something important to you that you do every day." (match: `important to you that you do every day`)
8. **Leadership Deep-Dive** — "Draw the org chart you're responsible for today." (match: `draw the org chart`)
9. **Passion** — "What is the worst job you could imagine? How would you create passion around it?" (match: `worst job you could imagine`)
10. **Continuous Improvement** — "What counts as work? When do you work, when don't you?" (match: `what counts as work`)

### Exceptions
None. If a candidate's profile calls for a probe the Form 8 set doesn't cover, that context belongs in the **coaching note** of the closest Form 8 question. If the Form 8 set is genuinely missing a question the framework needs, propose adding it to PROJECT_NOTES.md (as an 11th canonical question) and update `FORM8_QUESTIONS` in the build script before shipping.

## Section 10 — Recommendation
- [ ] `class="recommendation-badge"` — min 1
- [ ] `RECOMMENDATION_TEXT` is **summary pill text, not a paragraph block** (≤ 300 chars). Per Schott_Timothy 2026-04-27 build: the recommendation lives in a 12px gold inline pill and must read as a one-liner; longer narrative belongs in the Role-Fit Hard column or Targeted Concerns section, not the badge. Build-time `assert len(RECOMMENDATION_TEXT) <= 300`.

## Section 11 — Brand + Title + Tokens
- [ ] `HALE GLOBAL SUCCESS DIAGNOSTICS` appears ≥ 2 times
- [ ] Candidate full name appears ≥ 2 times
- [ ] `<title>` tag matches pattern `{Name} — {Role} | HALE GLOBAL SUCCESS DIAGNOSTICS`
- [ ] Header brand lockup is `HALE GLOBAL SUCCESS DIAGNOSTICS` (not bare `HALE GLOBAL`)
- [ ] Zero unreplaced `{{TOKEN}}` patterns in output

## Section 11b — Role-Fit Section Content (added 2026-04-27, Schott build)

The Role-Fit "What Will Be Hard" column must take a **step back to the wiring profile shape** before listing per-dimension concerns. This is non-negotiable for any CFO / control-function seat where the candidate's wiring quadrant matters.

- [ ] `ROLE_FIT_HARD` opens with a "Step back" / wiring-quadrant paragraph that names:
  - the canonical strong-CFO wiring quadrant (top-left of TTI wheel: Implementor + Conductor, high-D + high-C); for non-CFO seats, name the quadrant typical for that seat
  - where the candidate's Natural and Adapted positions sit relative to that quadrant
  - the size of the Natural→Adapted adaptation gap (especially S-compression > ~30 points), with the standard interpretation: large sustained adaptations are how leaders burn out of seats
- [ ] Build-time check: `ROLE_FIT_HARD` contains at least one of `top-left`, `top-right`, `bottom-left`, `bottom-right` (TTI quadrant reference) AND at least one of `Implementor`, `Conductor`, `Persuader`, `Promoter`, `Relater`, `Supporter`, `Coordinator`, `Analyzer` (TTI wedge name).

## Section 11c — Print / PDF Rendering Rules (added 2026-04-27, Schott build)

Renderer (`make_pdf_<slug>.js` / `render_<slug>_pdf.js`) MUST include all of the following CSS rules. Failure mode: titles strand at the bottom of one page while their content jumps to the next, leaving 200–500px of trailing whitespace.

- [ ] **`.role-fit-box` and `.concerns-box`** — `break-inside: avoid` (these are self-contained 2-column blocks small enough to fit one page; keep whole so the title stays attached to the columns).
- [ ] **`.probes-section` and `.probes-grid`** — `break-inside: auto` (the 10-card grid is too tall to keep whole; rely on per-card atomicity + title-keep-with-next instead).
- [ ] **Header keep-with-next** must include div-class titles (template uses `<div class="probes-title">`, `<div class="role-fit-col-label">`, `<div class="section-title">`, etc.) AND the in-box headers `.role-fit-box h3, .concerns-box h3`. The h-tag-only rule does not catch them.
- [ ] **Paired-selector `break-before: avoid`** rules to chain title→first-child:
  - `.probes-title + .probes-grid`
  - `.role-fit-box h3 + .role-fit-seat`
  - `.role-fit-seat + .role-fit-grid`
  - `.concerns-box h3 + .concern-item`
  - `.section-title + .timeline`, `.section-title + canvas`, `.section-title + p`
- [ ] After every render, eyeball the PDF for: stranded titles at page bottoms, large trailing whitespace, content split across pages where a small atomic unit (probe-card, concern-item, role-fit column) was bisected.

## Section 12 — Data Provenance
- [ ] L1 scores loaded from respondent `L1` sheet
- [ ] L2 scores loaded from respondent `L2` sheet column 5 `[Score5_filtered]`
- [ ] Population RF counts loaded from `Histogram Data.xlsx` / `Zalgo summ` column 7 (`@#RF`) — NOT from `Histogram Flags` sheet (that sheet is bin definitions only)
- [ ] Teach Items count loaded from `TeachTop10` sheet row count (should be 10)
- [ ] If any LinkedIn-dependent section (career, board roles, education) lacks source data: build FAILS with message instructing user to paste LinkedIn profile text

## Enforcement
The build script `build_<slug>_hiring.py` must run a `qa_gate()` function AFTER token
substitution and BEFORE saving the output. Every check above maps to one or more
assertions. Failure raises `AssertionError` with a listing of all failed items;
script exits non-zero.

Reference counts for parity (Bender_Jody):
```
concern-item>=2 concern-number=concern-item concern-text=concern-item wiring-flag=2 wiring-fit-content=1
timeline-block=6 timeline-legend=1 timeline-banner=1 legend-item=6
probe-card=10 probe-number=10 probe-category=10 probe-question=10 probe-coaching=10
recommendation-badge=1
```
