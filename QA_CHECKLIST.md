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

## Section 1 — Top 2 Concerns (now lives inside Interview section, added 2026-04-28, Houston build)

The standalone `<div class="concerns-box">` block has been **removed** from the main report flow. The two concerns are now relocated to the top of the Interview section as a compressed bridge-to-action framing for the Excellence Standards Interview Questions that follow. See METHODOLOGY.md *"Concerns are validation framing for the Interview"* for the structural rule.

- [ ] **Sub-header label is `2 Top Concerns`** (uppercase, no underline). Build script renders it as `<p style="...text-transform: uppercase; ...">2 Top Concerns</p>` inside the Interview section's grid container.
- [ ] **Concerns are a numbered ordered list** (`<ol>` with two `<li>` items), each ~80 words, full-width across the page.
- [ ] **Sub-header AND ordered-list wrapper both set `grid-column: 1 / -1;`** to span the full grid width — otherwise the parent `.probes-grid` (auto-fit, minmax 300px) squeezes them into single grid cells alongside the question cards.
- [ ] **Each concern references specific question numbers** by the canonical Form 8 question name + number (`Facilitative Mindset (question #6)`, `Talent Development (question #2)`, etc.) — the bridge-to-action linkage.
- [ ] **Concerns do NOT re-prove the diagnostic case.** That case lives in the Signature Pattern + Role-Fit Hard sections upstream. Compressed concerns name: the standards-pattern that identifies the concern, the open seat-fit question, the question numbers that target it.
- [ ] **No "Validate whether [standard] is real" or "Interview behavior is the test" framing** — see Section 11e (Standards-beat-the-interview principle). Use *"Use [question name] to surface..."* instead of *"Probe [question name] to validate..."*.
- [ ] Build-script regex check confirms no occurrence of `validate whether` / `interview behavior is the test` / `probe X to determine` in the rendered Concerns content.

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

## Section 9 — Excellence Standards Interview Questions (CRITICAL: Form 8 sourcing — display label updated 2026-04-28, Houston build)

**Form 8 sourcing is a non-negotiable contract.** Interview questions are drawn VERBATIM from the canonical Form 8 set defined in PROJECT_NOTES.md. They are NOT generated, NOT paraphrased, and NOT substituted. Freelanced questions are the failure mode the ExcStds methodology was built to replace. See PROJECT_NOTES.md `## Interview Questions (Form 8) — CRITICAL, NON-NEGOTIABLE` for the full rationale and exception policy.

**Display-label update (Houston build 2026-04-28):** the user-facing display labels are now:
- Section header: *"Interview — Validating the Targeted Concerns"* (was *"Interview Probes: Discovery & Validation"*)
- Sub-header for the question list: *"Excellence Standards Interview Questions"* (was *"Form 8 Probes (10 questions)"*)
- The internal taxonomy `FORM8_QUESTIONS` is unchanged — it remains the canonical 10-question source-of-truth set per PROJECT_NOTES.md. Only the user-facing display label changed.

The Interview section now also leads with the *"2 Top Concerns"* sub-section (see Section 1 above). The full Interview-section structure is:

```
Interview — Validating the Targeted Concerns

  2 TOP CONCERNS                            (uppercase sub-header, no underline, full grid width)
    1. Concern 1 — full-width, ~80 words
    2. Concern 2 — full-width, ~80 words

  EXCELLENCE STANDARDS INTERVIEW QUESTIONS  (uppercase sub-header, no underline, full grid width)
    [10 question cards in their natural grid layout]
```

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
- [ ] `HALE GLOBAL SUCCESS DIAGNOSTICS` appears ≥ 2 times (top banner + footer + PDF header + title; uppercase lockup locations)
- [ ] Candidate full name appears ≥ 2 times
- [ ] `<title>` tag matches pattern `{Name} — {Role} | HALE GLOBAL SUCCESS DIAGNOSTICS`
- [ ] Header brand lockup is `HALE GLOBAL SUCCESS DIAGNOSTICS` (not bare `HALE GLOBAL`)
- [ ] Zero unreplaced `{{TOKEN}}` patterns in output
- [ ] **Narrative-content brand-lockup check (added 2026-04-28, Bender coaching build):** ZERO occurrences of bare `Hale Global` (proper-case, used in narrative prose) without the full lockup `Hale Global Success Diagnostics` following. Build-script regex: `re.search(r'Hale Global(?!\s+Success Diagnostics)', html_text_content)` must return None. This catches the closing-note / signature-pattern / connection-narrative / driving-forces-implications cases where authored prose accidentally drops the `Success Diagnostics` half of the lockup. See METHODOLOGY.md *"Brand-lockup discipline applies to ALL narrative content"*.

## Section 11b — Role-Fit Section Content (added 2026-04-27, Schott build; expanded 2026-04-27, Armstrong build)

The Role-Fit "What Will Be Hard" column must take a **step back to the wiring profile shape** before listing per-dimension concerns. This is non-negotiable for any CFO / control-function seat where the candidate's wiring quadrant matters.

- [ ] `ROLE_FIT_HARD` opens with a "Step back" / wiring-shape paragraph.
- [ ] Build-time check: `ROLE_FIT_HARD` contains a TTI quadrant reference (top-left / top-right / bottom-left / bottom-right) **OR** the explicit `ACROSS` / `center-of-wheel` framing for un-anchored profiles, AND at least one TTI wedge name (Implementor / Conductor / Persuader / Promoter / Relater / Supporter / Coordinator / Analyzer).

### Section 11b.1 — Wheel position is REQUIRED, not optional (CRITICAL — added 2026-04-27, Armstrong build)

**ALWAYS read the wheel position from the TTI before drafting any wiring-fit narrative. Reading DISC scores in isolation is insufficient and has produced shipping-quality errors.** Per Armstrong_Patrick 2026-04-27 build: the report initially read C=75 in isolation and concluded "canonical strong-CFO wiring, top-left quadrant." The actual TTI wheel positions were **Natural 60 (Promoting Analyzer, ACROSS) and Adapted 56 (Analyzing Implementor, ACROSS)** — both marked ACROSS, meaning **center-of-wheel, no strong anchor in any wedge**. Center-of-wheel profiles correlate with **lower success rates across all positions**; that read is the inverse of what "high C" implies in isolation. The wheel page (typically pages 25–27 in the TTI Executive PDF) is the source of truth.

**Hard rules for every wiring-fit narrative:**

1. Read the TTI wheel page. Record the Natural position number (1–60), the Natural wedge label, and whether it is marked **ACROSS** (transitional / between-wedges / center). Same for Adapted.
2. Cite the position number AND the wedge label AND the ACROSS marker (when present) explicitly in the wiring narrative. Phrasing like *"Natural position 60, Promoting Analyzer (ACROSS)"* is the standard.
3. Three structural reads to keep distinct:
   - **Anchored in role-aligned wedge** — wedge matches the seat's canonical demand (e.g., Implementor / Conductor for CFO). This is the success-correlated read.
   - **Anchored in wrong wedge** — clearly anchored in a wedge that is NOT what the seat rewards (e.g., Persuader / Promoter for CFO). This is what Schott_Timothy showed.
   - **ACROSS / center-of-wheel** — not anchored in any wedge; generalist profile. Correlates with lower base-rate success across positions. This is what Armstrong_Patrick showed. **Do NOT mistake high C alone for an Implementor anchor; the wheel position is the source of truth.**
4. Build-time check: any narrative that uses the phrases *"top-left,"* *"canonical CFO wiring,"* *"right wiring,"* *"Implementor quadrant,"* etc. MUST also cite the actual wheel position number. The qa_gate enforces this — see `build_<slug>_hiring.py`.

### Section 11b.1.1 — Standard Map N/A marker intensity formula (added 2026-04-27, Armstrong build)

Per Armstrong_Patrick 2026-04-27 build: the Standard Map dial's N (Natural) and A (Adapted) marker positions are computed from an `intensity` value (0..1) that controls how far from the center of the wheel each marker sits. The canonical mapping:

- Strongly-anchored DISC profiles → markers pushed toward the outer edge (intensity high)
- ACROSS / center-of-wheel profiles → markers pulled toward the center (intensity low)

**Wrong model (do not use):** `intensity = max_disc / 100` or `intensity = (C + S) / 200`. The Schott build shipped with `(C + S) / 200`, which produced an Armstrong intensity of 0.75 in early drafts — contradicting the ACROSS positioning the TTI wheel actually showed.

**Right model (canonical going forward):** mean-absolute-deviation from a 50/50/50/50 baseline, floored at 0.10. Implemented as `compute_intensity_from_disc(disc)` in `_pipeline/src/pipeline/motivators_section.py`.

- [ ] Build script imports `compute_intensity_from_disc` from `pipeline.motivators_section` and uses it for both `nat_intensity` and `adp_intensity` rather than computing intensity ad-hoc.
- [ ] Visual sanity-check after rendering: ACROSS profiles render N/A markers near the inner ring; clearly-anchored profiles render them at moderate-to-far-from-center radius.

### Section 11b.2 — Two-Sport Athlete is a holistic capacity-to-grow read, not a varsity-sport checkbox (added 2026-04-27, Armstrong build)

Per Armstrong_Patrick 2026-04-27 build: the radar dimension `Two-Sport Athlete` is shorthand for **the holistic Talent-axis read on capacity to grow**, not a literal varsity-sport check. The right questions are:

1. Has this person been **promoted consistently** across roles?
2. Does the LinkedIn record show **greatness in more than one area** (cross-domain excellence — board, advisory, athletic, civic, intellectual-public-output, founder)?
3. Does the arc **suggest capacity to grow** into the next altitude — i.e., are the next-step roles successively bigger / harder / higher-altitude?

Score the radar dimension on the integrated read of all three lenses, not on whether varsity sports appear on LinkedIn. Strong external signals (Big-4 Partner, NYSE-CFO, multiple awards, sustained board-level service, published writing) do NOT need to be paired with athletic distinction — they ARE Talent evidence on their own. Conversely, a varsity-sport line in college **without** the consistent-promotion / cross-domain-greatness pattern is not enough to score above 2 or 3.

The narrative prose for this radar dimension must reflect the holistic frame, not a checkbox. *"No varsity sports listed on LinkedIn"* on its own is the wrong frame.

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

## Section 11d — Signature Pattern Block (added 2026-04-28, Houston build)

The Signature Pattern block sits between the Recommendation badge and the Three-Axes cards. It is the cohesive prose read of the Excellence-Standards pattern as the file lands for THIS seat type. See METHODOLOGY.md *"Signature Pattern block — cohesive Excellence-Standards read"* for full specification.

- [ ] **Block exists.** `<div class="signature-pattern-box">` (or equivalent token-rendered block) is present, sitting after the recommendation-badge and before the three-axes section.
- [ ] **Header is `Signature Pattern — Excellence Standards Read`** (or a documented seat-specific variant).
- [ ] **One-sentence headline** in plain English at the top.
- [ ] **L1 sub-section first** with sub-header *"Where the L1 standards land negatively"* (uppercase, no underline). Each weak L1 in plain-English form: *"#N L1-Name SCORE — plain-English description."* L2 sub-scores live in the Dimensional Scorecard chart, NOT in this prose.
- [ ] **Flags sub-section second** with sub-header *"Flags lit"* (uppercase, no underline). Each lit flag named at full universal weight in plain English. Related flags can be grouped.
- [ ] **Italicized seat-reflection paragraph last** (~80–110 words). Makes an explicit opinion call: *"For [seat type], this profile is **MORE concerning / NEUTRAL / LESS concerning** than the same profile would be in a generic leadership seat."* The "why" anchors in what the function specifically does.
- [ ] **Plain-English discipline.** Build-script regex check: the L1 and Flags sections contain ZERO occurrences of jargon strings — `replacement-development`, `followership-and-replacement`, raw `L2 X.Y` references, wedge names like `Coordinator/Supporter`, or DF cluster names. Translate to plain language.
- [ ] **Length target.** Total block 200–300 words. Soft warn at 320, hard fail at 400.
- [ ] **Standards-universal discipline.** No "dispositive for X seat" or "less relevant for Y seat" phrasing in the L1 or Flags sections. The seat-judgment lives ONLY in the bottom italicized paragraph.

## Section 11e — Three-Axes Card Crispness Rule (added 2026-04-28, Houston build)

Each Three-Axes card body is the **interpretation** — the badge call, in 2–3 tight paragraphs. Supporting evidence lives in the Signature Pattern block, the chart panels, and the Targeted Concerns / Role-Fit sections — NOT in the axis card body.

- [ ] **Talent card target ≤200 words.** Anchored on the holistic three-lens read (consistent promotions / cross-domain greatness / capacity to grow into next altitude).
- [ ] **Judgment card target ≤200 words.** Anchored on **L1 #8 Organizational Decision Making** specifically, with L2 8.2 Clarity of Accountability and L2 8.7 Facts Over Feelings as the canonical sub-dimensions. **Other lit-flag concerns (Urgency, Conducting, Not Pleasing, etc.) are NOT routed into the Judgment card body** — they live in the Signature Pattern (cohesive read) and Concerns / Role-Fit (interview implications). The Judgment card explicitly notes that other concerns are addressed elsewhere.
- [ ] **Skills card target ≤120 words.** Domain credentials in one paragraph + wiring-fit conclusion in one short paragraph or sentence pointing to the Wiring-Fit panel below for full read. **No re-rendering of DISC scores, DF clusters, wheel-position descriptions, or wedge labels.**
- [ ] **Build-script word-count check (qa_gate):** warn at 220 / 220 / 140 words for Talent / Judgment / Skills; fail at 280 / 280 / 180.
- [ ] **Build-script content check:** Skills card does NOT contain `D=N` or `I=N` or `S=N` or `C=N` numeric DISC patterns (those live in the DISC chart panel only).
- [ ] **Build-script content check:** Judgment card does NOT enumerate L1 #1, #2, #3, #4, #5, #6, #7, #9 — only L1 #8 plus its sub-L2s. Other L1 references should appear in the Signature Pattern, Concerns, or Role-Fit sections.

## Section 11f — Standards-Beat-the-Interview Principle (added 2026-04-28, Houston build)

The instrument-flagged Excellence-Standards concerns ARE the concerns. Interview questions are tools for surfacing behavioral detail on already-identified concerns, not tests of whether the instrument was right. See METHODOLOGY.md *"Standards-beat-the-interview principle"*.

- [ ] **No "Validate whether [standard] is real" framing** in Concerns or Interview sections.
- [ ] **No "Interview behavior is the test" framing** anywhere in the rendered HTML.
- [ ] **No "Probe X to determine if Y is true" framing.** Use *"Use [question name] to surface..."* instead of *"Probe [question name] to validate..."*.
- [ ] **Build-script regex check (qa_gate):** assert ZERO occurrences of:
  - `validate whether`
  - `interview behavior is the test`
  - `probe X to determine`
  - `test whether the standard`
  in the rendered Concerns + Interview-section content.
- [ ] **Allowed framing patterns:**
  - *"The signature pattern names a clear [X] gap. Use [question name] to surface the behavioral detail."*
  - *"Bottom-decile [Y] describes a [Y] gap. Use [question name] to surface a recent specific case."*
  - *"The open seat-fit question is whether [demonstrated competence] travels to a new company without [the supporting context]."*

## Section 11g — Coaching-guide L2 color tags (Variant 1 only — added 2026-04-28, Bender coaching build)

Every Impact and Teach card in a Variant 1 coaching guide MUST end with a `<div class="practice-l2-tag">` containing the L2 number and short name (e.g., `8.1 Simplification Methods`). The tag renders as a long horizontal pill in the upper-right of each card and must color-match the wedge color used for that L2 in the respondent's Motivators wheel. See METHODOLOGY.md *"Coaching-guide L2 color tags — every Impact and Teach card MUST carry one"* for the full rule.

- [ ] **Per-card practice-l2-tag presence.** Every `<div class="practice-item">` (Impact card) AND every `<div class="practice-item">` inside the Teach section MUST be paired with a `<div class="practice-l2-tag" ...>` element. Build-script qa_gate: `count('practice-l2-tag')` ≥ `count('practice-item')` minus the count of subsection-header divs. For a typical coaching guide with ~12 Impact cards (3-4 flag-driven + 8-9 per-answer) plus ~10 Teach cards = ≥22 practice-l2-tag elements.
- [ ] **Color-bucket discipline.** Each tag's inline `style` MUST set `background`, `color`, AND `border-color` to one of the canonical 5-bucket palette colors (motivator_strong blue `#2563eb` / motivator_weak red `#c0392b` / anti_strong green `#22c55e` / anti_weak gold `#d4a84b` / off-wheel gray `#f3f4f6`). The text-color and border-color must produce sufficient contrast (white text on dark fills, dark text on pale fills).
- [ ] **L2 number + name format.** Tag content is `<L2_number> <L2_short_name>` (e.g., `8.1 Simplification Methods`). The `data-l2` attribute must match the L2 number in the displayed text.
- [ ] **Build-script qa_gate check.** Add: `if html.count('practice-l2-tag') < expected_card_count: failures.append(f"S11g: practice-l2-tag missing on {expected_card_count - count} cards")`. Fails the build if any Impact or Teach card is missing its L2 tag.
- [ ] **The Bender coaching guide (April 2026) shipped without ANY practice-l2-tag elements on its 22 cards.** This was the regression that drove this rule's codification. Future coaching builds inherit the rule via the qa_gate check.
- [ ] **L2 tag placement: upper-right of the card header row, NOT bottom of the card.** The tag must be a sibling of the inner `<div style="flex:1;">` (which holds title + qref), inside the outer `<div style="display:flex; align-items:baseline; gap:12px;">` that wraps practice-num + title + qref + L2 tag. CSS `flex-shrink:0` + `align-self:flex-start` on `.practice-l2-tag` combined with `flex:1` on the title-and-qref div is what positions the tag to the right edge of the header. See METHODOLOGY.md *"Implementation pattern — EXACT structural placement"* for the canonical HTML.
- [ ] **Card structural integrity check (added 2026-04-28, Bender v5):** practice-body MUST be inside practice-item, not a sibling of it. Build-script qa_gate regex check: for each `<div class="practice-item">` opening, the next `<div class="practice-body">` must occur BEFORE the matching `</div>` that closes the practice-item. Three known bugs to detect:
  - **Spurious extra `</div>` between close-outer-flex and `<div class="practice-body">`** → closes practice-item too early, kicks body out of card. Renders body unstyled below the card with no border/padding.
  - **L2 tag nested inside `flex:1` instead of sibling-of-flex:1** → tag stacks below qref instead of floating right. Detected by counting `<div style="flex:1;">` opens vs `</div>` closes between qref and tag — opens minus closes must equal zero.
  - **L2 tag placed after practice-body close instead of inside header row** → tag renders at bottom of card. Detected by checking that practice-l2-tag appears BEFORE practice-body in the source order for each card.

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

## Section 11h — Coaching-guide practice-fuel routine box (Variant 1 only — added 2026-04-28, Bender coaching build)

Every Impact card AND every Teach card in a Variant 1 coaching guide MUST carry a `<div class="practice-fuel">` element containing a one-paragraph routine starting with the literal word "Routine" (Impact cards) or "Routine to protect" (Teach cards). The fuel renders as a yellow callout box at the bottom of the card and is the actionable behavioral routine that distinguishes a coaching card from a generic descriptive card. See METHODOLOGY.md *"Coaching-guide practice-fuel — every Impact and Teach card MUST carry one"* for the full rule.

- [ ] **Per-card practice-fuel presence.** `count('class="practice-fuel"') == count('class="practice-item"')`. Build-script qa_gate: assert exact equality. Bender shipped without practice-fuel on 19 of 22 cards in v6 — this regression is what drove this rule's codification.
- [ ] **Fuel content begins with the word "Routine".** Build-script regex: every `practice-fuel` div's text content must match `^Routine` (case-insensitive). Teach cards may use `Routine to protect`. Impact and flag cards use plain `Routine`.
- [ ] **Structural placement: practice-fuel is a SIBLING of practice-body INSIDE practice-item.** Canonical card structure:

```
<div class="practice-item">
  <div style="display:flex; ...">                       <!-- header row -->
    <span class="practice-num">N</span>
    <div style="flex:1;"><title /><qref /></div>
    <div class="practice-l2-tag" ...>L2 NAME</div>      <!-- upper-right pill -->
  </div>
  <div class="practice-body">
    <p>...</p>
  </div>
  <div class="practice-fuel">Routine: ...</div>         <!-- yellow callout -->
</div>
```

- [ ] **Closing `</div>` MUST follow practice-fuel.** Bender flag cards 1, 2, 3 in v5–v6 had `practice-fuel` as the last sibling but were missing the close-practice-item `</div>`, which caused the next card to nest INSIDE the previous one in DOM. The visible symptoms were: stacked vertical gold left-borders (multiple practice-item border-lefts piled at the page edge) AND `break-inside:avoid` on the outer (now-deeply-nested) practice-item forcing the entire nested tree to be treated as one un-breakable card, which produced massive whitespace and stranded subsection-headers. **Build-script qa_gate regex:** for each `<div class="practice-item` opener in the rendered HTML, the next `<div class="practice-item` opener (or end of practice-section) must be preceded by an *equal-or-greater* number of `</div>` close tags such that the nesting depth returns to the practice-section level. The Python helper `_pipeline/scripts/_qa_helpers.py:assert_practice_item_balanced(html)` runs this check.
- [ ] **Build-script qa_gate must fail the build** if any of: (a) `count(practice-fuel) != count(practice-item)`, (b) any `practice-fuel` text content does not start with `Routine`, (c) any practice-item is unclosed at the next sibling boundary.

## Section 11i — Coaching-guide print-CSS pagination contract (Variant 1 only — added 2026-04-28, Bender coaching build)

The render script `render_<slug>_coaching_pdf.js` MUST inject a print stylesheet via `page.addStyleTag` BEFORE the PDF is generated. The stylesheet has THREE non-negotiable parts. Failure produces stranded headers, multi-line indents, or chart-title-without-canvas splits like the ones Bender v6–v8 exhibited.

### 11i.1 — Atomic blocks (`break-inside: avoid`)

These blocks MUST be kept on a single page; they are small enough to fit on any page they land on:

- [ ] `.practice-item` — every Impact and Teach card.
- [ ] `.practice-fuel` — the yellow callout (separate rule because it can appear inside practice-item OR as standalone).
- [ ] `.practice-subsection-hdr`, `.practice-subsection-hdr-title`, `.practice-subsection-hdr-blurb` — the multi-line subsection header block (e.g., FLAG-DRIVEN ITEMS, PER-ANSWER IMPACT ITEMS, TEACH ITEMS). Without this rule, the title can split from its blurb across pages.
- [ ] `.dist-section` — the entire Population Distribution section (~325px tall: title + chart key + 3 histograms in a grid). Without this rule, the title + chart key end up at the bottom of one page and the histograms jump to the next.
- [ ] `.dist-chart-panel` — each individual histogram panel (defensive; should rarely matter when `.dist-section` is atomic).
- [ ] All atomic-card classes from hiring reports: `.callout, .bucket, .probe-card, .award-card, .board-role-card, .axis-card, .concern-card, .metric-card, .l2-row, .timeline-block, .timeline-row, .dimension-row, .flag-chip, .scorecard-row, .probe, .concern, .wiring-row, .htl-item`.

### 11i.2 — Title-keep-with-next (`break-after: avoid`)

These element classes MUST have `break-after: avoid` so the immediately-following content is pulled with them:

- [ ] `h1, h2, h3, h4, h5, h6` (defensive baseline).
- [ ] `.section-title` (Population Distribution, DISC Profile, Excellence Standards Dimensional Scorecard, Career Timeline).
- [ ] `.subsection-title`.
- [ ] `.practice-subsection-hdr` AND `.practice-subsection-hdr-title` — both required because the multi-line block can break-after either at the outer wrapper OR the inner title.
- [ ] `.practice-header` — Part 1 / Part 2 (What You Teach / What to Work On). **Bender v9 stranded "Part 2" because this was missing.** The h-tag rule does not catch class-styled divs.
- [ ] `.practice-subtitle` — sits between `.practice-header` and `.practice-subsection-hdr`.
- [ ] `.metrics-title`, `.fingerprint-title` — Headline Metrics + Behavioral Fingerprint titles.
- [ ] `.dist-chart-title`, `.dist-chart-key` — Population Distribution chart panel titles + chart-key strip.
- [ ] `.bucket-pill, .card-title, .practice-item-title, .axis-title, .concern-title, .probe-title` — atomic card-internal titles.

### 11i.3 — Paired-selector keep-with-previous (`break-before: avoid`)

For every header class in 11i.2, at least one paired `+ next-sibling` selector must lock the keep-with-next from the other side:

- [ ] `h2 + p, h3 + p, h4 + p` — defensive.
- [ ] `.section-title + p, .subsection-title + p` — paragraph-following.
- [ ] `.section-title + .timeline` — Career Timeline + first row.
- [ ] `.section-title + canvas` — DISC Profile chart attachment.
- [ ] `.practice-subsection-hdr + .practice-item` — REQUIRED for FLAG-DRIVEN ITEMS / PER-ANSWER IMPACT ITEMS / TEACH ITEMS to keep with their first card.
- [ ] `.practice-header + .practice-subtitle` — Part 1/2 + subtitle.
- [ ] `.practice-subtitle + .practice-subsection-hdr` — subtitle + first subsection header.
- [ ] `.metrics-title + .metrics-grid` — Headline Metrics title + grid.
- [ ] `.fingerprint-title + p` — Behavioral Fingerprint title + first paragraph.
- [ ] `.section-title + .dist-chart-key` — Population Distribution title + chart key (also covered by `.dist-section` atomic rule).

### 11i.4 — Auto-break overrides (`break-inside: auto`)

Containers larger than a page MUST allow normal pagination:

- [ ] `.section, .practice-section, .fingerprint, .metrics, .header`.
- [ ] `.wiring-panel, .alignment-grid, .callouts-pair, .dist-chart, .ma-section, .career-timeline, .timeline-group`.
- [ ] `.three-axes, .concerns, .interview-probes, .wiring-fit`.

### 11i.5 — Canvas height preservation

- [ ] `canvas { max-width: 100% !important; height: auto !important; }`. The `height: auto` is REQUIRED. Without it, Chart.js's responsive resize observer can clear the canvas drawing buffer mid-pagination, leaving titled-but-empty chart panels. Bender v11 demonstrated the regression — all 5 canvases reported `false` from the canvasCheck after dropping `height: auto`.

### 11i.6 — Render-script canvas health-check

- [ ] After `addStyleTag` and the 1.8s settle wait, query `document.querySelectorAll('canvas')` and read pixel data via `getImageData`. If ANY canvas has zero non-white pixels, abort with `process.exit(2)` BEFORE generating the PDF. This is what surfaced the v11 regression in seconds.

### 11i.7 — Source-of-truth file integrity

- [ ] Both `render_<slug>_coaching_pdf.js` and `coaching_guide_TEMPLATE.html` are susceptible to OneDrive sync truncation when the Edit tool writes them. After ANY change to either: (a) `node --check render_<slug>_coaching_pdf.js`, (b) confirm the template ends with `</html>`, (c) rebuild and inspect the rendered HTML's last 100 bytes for `</html>`. If truncated, restore the missing tail from `git show HEAD:<file>` before re-running the render.
