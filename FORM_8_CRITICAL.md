# Form 8 — CRITICAL, NON-NEGOTIABLE Policy for Interview Probes

> **This document is the source of truth for the Form 8 interview-probe policy in the ExcStds hiring-report pipeline.** PROJECT_NOTES.md, QA_CHECKLIST.md, and the build scripts all implement this policy. If the skills-plugin `SKILL.md` is updated in the future, it must inherit from this file — not the reverse.

## The policy in one sentence

Every hiring report contains 10 interview probe cards, and the 10 questions in those cards are drawn verbatim from the canonical Form 8 set defined in this document. The questions themselves are not discretionary. The category label and coaching note under each question are tailored to the specific candidate; the question text is not.

## Why this is non-negotiable

1. **Cross-candidate calibration.** Form 8 is the reference instrument that makes candidate A and candidate B comparable. If each report generates novel questions, every interview becomes incomparable to the last — the hiring manager loses the ability to build a mental library of how great, good, and mediocre answers to the same question distinguish themselves.
2. **Trained pattern recognition.** The probes are designed to surface specific, documented behavioral signals (Two-Sport Athlete, Punctuates Differently, Pre-Proof Belief, etc.). Novel interviewer-generated questions do not surface those signals reliably; they test whatever the interviewer was thinking about that morning.
3. **Freelanced questions silently substitute the interviewer's intuition for the instrument.** That is precisely the failure mode the entire ExcStds methodology was built to replace. The value of the instrument is that it asks the same standardized questions of every candidate; abandoning that for report-generation convenience collapses the instrument's value.

## The 10 canonical Form 8 questions (probes 1–10, in canonical order)

| # | Dimension | Question | QA match substring |
|---|-----------|----------|--------------------|
| 1 | Two-Sport Athlete | "Of all the things you've done in life, tell me what results you're most proud of." | `most proud of` |
| 2 | Talent Development | "What people over your career have you nurtured who have gone on to do great things?" | `nurtured who have gone on` |
| 3 | TORC | "What was your boss's name? What will they say your strengths and areas for improvement were?" | `strengths and areas for improvement` |
| 4 | Emotional Maturity | "What's the greatest adversity you've faced in life?" | `greatest adversity` |
| 5 | Punctuates Differently | "What do you do to achieve excellence that others don't?" | `achieve excellence that others don` |
| 6 | Facilitative Mindset | "What's something you really believe in? When is it okay to make exceptions?" | `okay to make exceptions` |
| 7 | Commitment | "Tell me something important to you that you do every day." | `important to you that you do every day` |
| 8 | Leadership Deep-Dive | "Draw the org chart you're responsible for today." | `draw the org chart` |
| 9 | Passion | "What is the worst job you could imagine? How would you create passion around it?" | `worst job you could imagine` |
| 10 | Continuous Improvement | "What counts as work? When do you work, when don't you?" | `what counts as work` |

## What IS tailored per candidate — and what stays faithful

- **Tailored:** the `.probe-category` label (e.g., `"FACILITATIVE MINDSET (Concern 1 · Decisions-over-feelings)"`) — links the Form 8 question to this candidate's specific flag, concern, or wiring signal.
- **Tailored:** the `.probe-coaching` note — grounded in this candidate's career history, flag profile, wiring mismatches. No `"Listen for:"` prefix.
- **Not tailored:** the `.probe-question` text. Do not paraphrase, do not re-order, do not substitute a "similar" question, do not generate novel questions even if they seem better calibrated to this specific candidate.

## Display rule

Do NOT lead the probe-question display text with the `"Form 8 #N —"` label. The reader sees the canonical question in quotes exactly as it will be asked in the interview. "Form 8" is a sourcing rule (which questions are allowed), not a display label. The probe-category label carries the instrument-framing context.

## Build-time enforcement

The build script `_pipeline/scripts/build_<slug>_hiring.py` contains a module-level constant `FORM8_QUESTIONS` — a list of `(dimension_name, canonical_question_text, qa_match_substring)` tuples. The `qa_gate()` function matches each canonical substring against the rendered `.probe-question` blocks. If fewer than 10 of the 10 canonical questions are present, the build FAILS with `AssertionError`. Freelanced or missing questions cannot ship.

```python
# Enforcement logic in qa_gate():
probe_questions = re.findall(
    r'<div class="probe-question">(.*?)</div>', html, re.DOTALL
)
if len(probe_questions) == 10:
    matched_substrs = set()
    for q_html in probe_questions:
        q_lower = q_html.lower()
        for (_name, _canonical, substr) in FORM8_QUESTIONS:
            if substr.lower() in q_lower:
                matched_substrs.add(substr)
                break
    if len(matched_substrs) < 10:
        failures.append("S9-Form8: ...")
```

## Exceptions

**None.** If a candidate's profile seems to call for a probe the Form 8 set doesn't cover, that context belongs in the **coaching note** of the closest Form 8 question — not in a substituted question.

If the Form 8 set is genuinely missing a question the framework needs (an edge case that should be rare), the path forward is:

1. Propose adding the new question as an 11th canonical question to this document and to PROJECT_NOTES.md.
2. Update `FORM8_QUESTIONS` in every active `build_<slug>_hiring.py`.
3. Update `QA_CHECKLIST.md` Section 9's canonical table with the new entry and match substring.
4. Ship the addition before generating any new reports that use it.

Do **not** silently substitute a novel question in a single report. That is how calibration decays.

## Pointer for the skills-plugin SKILL.md

When the skills-plugin `report/SKILL.md` is next edited, add a `CRITICAL — Interview Probes from Form 8` block that mirrors this document. The block should live between the `**CRITICAL — Satisfied with Gripes Flag...**` section and `#### Key Principles`. SKILL.md should reference this file (`_pipeline/FORM_8_CRITICAL.md`) as the authoritative policy source.
