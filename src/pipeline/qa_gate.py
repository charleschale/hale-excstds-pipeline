"""Shared qa_gate functions for hiring + coaching builds.

Codifies the cross-build rules that should fail any build attempt before HTML
is written. New builds should `from pipeline.qa_gate import qa_gate_coaching`
or `qa_gate_hiring` and call it from their main(); they should NOT re-implement
these checks inline.

Rules enforced (as of 2026-04-28, Bender coaching build):
- S11g: every Impact and Teach card has a practice-l2-tag (coaching only)
- S11h: every Impact and Teach card has a practice-fuel starting with "Routine"
- S11h: practice-item open/close balance (no nested cards from missing close-divs)
- General: no unreplaced {{TOKEN}} placeholders
- General: every named canvas id is present in the HTML
"""
import re

# ---------------------------------------------------------------------------
# Generic checks shared by both variants
# ---------------------------------------------------------------------------

def _check_unreplaced_tokens(html, failures):
    leaks = re.findall(r"\{\{([A-Z_0-9]+)\}\}", html)
    if leaks:
        failures.append(f"Unreplaced tokens: {sorted(set(leaks))}")


def _check_canvases(html, canvas_ids, failures):
    for cid in canvas_ids:
        if f"id=\"{cid}\"" not in html:
            failures.append(f"Canvas missing: {cid}")


def _check_brand_lockup(html, min_count, failures):
    if html.count("HALE GLOBAL SUCCESS DIAGNOSTICS") < min_count:
        failures.append(f"Brand lockup count < {min_count}")


# ---------------------------------------------------------------------------
# Coaching-specific S11g (L2 tags) and S11h (practice-fuel + structural balance)
# ---------------------------------------------------------------------------

def _check_practice_l2_tag(html, failures):
    """S11g: every practice-item must have a paired practice-l2-tag."""
    n_items = (
        html.count('class="practice-item"') +
        html.count('class="practice-item flag-driven"')
    )
    n_tags = html.count('class="practice-l2-tag"')
    if n_tags < n_items:
        failures.append(
            f"S11g: practice-l2-tag count ({n_tags}) < practice-item count ({n_items}) "
            f"— missing L2 tag on {n_items - n_tags} card(s). Every Impact and Teach "
            f"card must end with a practice-l2-tag using motivators-wheel colors."
        )


def _check_practice_fuel(html, failures):
    """S11h: every practice-item must have a paired practice-fuel; content begins with 'Routine'."""
    n_items = (
        html.count('class="practice-item"') +
        html.count('class="practice-item flag-driven"')
    )
    n_fuel = html.count('class="practice-fuel"')
    if n_fuel != n_items:
        failures.append(
            f"S11h: practice-fuel count ({n_fuel}) != practice-item count ({n_items}). "
            f"Every Impact and Teach card MUST end with a practice-fuel div."
        )

    fuel_re = re.compile(r'<div class="practice-fuel">([^<]*)')
    bad = [
        m.group(1)[:60]
        for m in fuel_re.finditer(html)
        if not m.group(1).lstrip().lower().startswith("routine")
    ]
    if bad:
        failures.append(
            f"S11h: {len(bad)} practice-fuel block(s) do not start with 'Routine': "
            f"{[s[:40] for s in bad[:3]]}"
        )


def _check_practice_item_balance(html, failures):
    """S11h structural-integrity: practice-item open/close balance.

    For each `<div class="practice-item">` opener, the next opener must be
    preceded by an equal number of `<div>` opens and `</div>` closes. If a card
    is missing its close-practice-item div, the next sibling card opens nested
    inside the previous and produces stacked vertical gold left-borders.
    """
    item_open_re = re.compile(r'<div class="practice-item(?:"|\s+flag-driven")')
    closes_re = re.compile(r'</div>')
    opens_re = re.compile(r'<div\b')
    positions = [m.start() for m in item_open_re.finditer(html)]
    for i in range(len(positions) - 1):
        between = html[positions[i] : positions[i + 1]]
        opens = len(opens_re.findall(between))
        closes = len(closes_re.findall(between))
        if opens != closes:
            failures.append(
                f"S11h: practice-item structural imbalance between cards {i+1} and {i+2}: "
                f"{opens} opens vs {closes} closes between them. Each card MUST close "
                f"its practice-item div before the next opens."
            )
            break


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------

DEFAULT_COACHING_CANVASES = (
    "distChart1", "distChart2", "distChart3", "discChart", "excstdsChart",
)
DEFAULT_HIRING_CANVASES = (
    "discChart", "excstdsChart",
)


def qa_gate_coaching(html, *, expected_teach=10, expected_impact_flag=3,
                      expected_impact_std=9, canvas_ids=DEFAULT_COACHING_CANVASES,
                      candidate_name=None, extra_checks=None):
    """Run the standard coaching-guide qa_gate. Raises AssertionError on failure.

    Build scripts call this AFTER token substitution and BEFORE writing the file.
    """
    failures = []
    _check_unreplaced_tokens(html, failures)
    _check_canvases(html, canvas_ids, failures)
    _check_brand_lockup(html, min_count=2, failures=failures)
    _check_practice_l2_tag(html, failures)
    _check_practice_fuel(html, failures)
    _check_practice_item_balance(html, failures)

    # Section-count check
    try:
        teach = html.split("Part 1 — What You Teach")[1].split("Part 2 — What to Work On")[0]
        impact = html.split("Part 2 — What to Work On")[1].split("How the Two Lines Connect")[0]
    except IndexError:
        failures.append("Could not split on Part 1 / Part 2 / How the Two Lines Connect")
        teach, impact = "", ""
    n_teach = teach.count('class="practice-item"')
    n_impact_std = impact.count('class="practice-item"')
    n_impact_flag = impact.count('class="practice-item flag-driven"')
    if n_teach < expected_teach:
        failures.append(f"Teach items: got {n_teach}, need >= {expected_teach}")
    if n_impact_flag < expected_impact_flag:
        failures.append(f"Flag-driven impact items: got {n_impact_flag}, need >= {expected_impact_flag}")
    if n_impact_std < expected_impact_std:
        failures.append(f"Per-answer impact items: got {n_impact_std}, need >= {expected_impact_std}")

    # Candidate-name spot check (optional)
    if candidate_name and candidate_name not in html:
        failures.append(f"Candidate name missing: {candidate_name}")

    if extra_checks:
        extra_checks(html, failures)

    print()
    print("=== QA GATE (coaching) ===")
    if failures:
        print(f"*** QA GATE FAILED: {len(failures)} issue(s) ***")
        for f in failures:
            print(f"  - {f}")
        raise AssertionError(f"QA gate failed with {len(failures)} issue(s)")
    print("*** QA GATE PASSED ***")


def qa_gate_hiring(html, *, canvas_ids=DEFAULT_HIRING_CANVASES,
                    candidate_name=None, extra_checks=None):
    """Run the standard hiring-report qa_gate. Raises AssertionError on failure."""
    failures = []
    _check_unreplaced_tokens(html, failures)
    _check_canvases(html, canvas_ids, failures)
    _check_brand_lockup(html, min_count=2, failures=failures)
    if candidate_name and candidate_name not in html:
        failures.append(f"Candidate name missing: {candidate_name}")
    if extra_checks:
        extra_checks(html, failures)

    print()
    print("=== QA GATE (hiring) ===")
    if failures:
        print(f"*** QA GATE FAILED: {len(failures)} issue(s) ***")
        for f in failures:
            print(f"  - {f}")
        raise AssertionError(f"QA gate failed with {len(failures)} issue(s)")
    print("*** QA GATE PASSED ***")
