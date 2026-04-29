"""TEMPLATE: Excellence Standards Hiring Manager Report build script.

Fork this for the next hiring-report build. The candidate-specific narrative
content lives in the `# === CANDIDATE-SPECIFIC ===` blocks; everything else
(data loading, motivators section, qa_gate) is inherited from shared modules.

Source-of-truth references:
- Three-Axes card crispness:    METHODOLOGY.md "Three-Axes Card Crispness Rule"
- Signature Pattern block:      METHODOLOGY.md "Signature Pattern block"
- Wheel-position rule:          METHODOLOGY.md "Wheel position is the source of truth"
- Standards-beat-the-interview: METHODOLOGY.md / QA 11f
- Brand-lockup discipline:      METHODOLOGY.md
- qa_gate enforcement:          pipeline.qa_gate.qa_gate_hiring()
- Print-CSS contract:           _print_css.json (consumed by render script)

Run from repo root:
    python _pipeline/scripts/build_<slug>_hiring.py
"""
import json
import re
import sys
from pathlib import Path
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "_pipeline" / "src"))

from pipeline.motivators_section import build_section, compute_intensity_from_disc
from pipeline.qa_gate import qa_gate_hiring

# =================== EDIT THESE FOR EACH NEW BUILD ===================
SLUG          = "TODO_lastname_firstname"
CANDIDATE     = "TODO First Last"
CANDIDATE_FN  = "TODO First"
RESPONDENT_ID = "TODO_email_or_id"
REPORT_DATE   = "TODO Month DD, YYYY"
SEAT_TYPE     = "TODO seat type (CFO / HR-VP / etc.)"
RECOMMENDATION = "TODO: HIRE / RECOMMEND AGAINST / QUALIFIED YES"
# =====================================================================

RESPONDENT_XLSX = ROOT / "_respondents" / RESPONDENT_ID / "data.xlsx"
HISTOGRAM_XLSX  = ROOT / "Histogram Data.xlsx"
TEMPLATE        = ROOT / "_templates" / "hiring_report_TEMPLATE.html"
OUT_DIR         = ROOT / "_reports"
OUT             = OUT_DIR / f"{SLUG}_hiring_report.html"


# ============================================================================
# DATA LOADING (copy from build_houston_hiring.py — most recent canonical impl)
# ============================================================================

def load_respondent_data():
    """Load L1, L2, DISC, DF, flags, etc. from respondent xlsx."""
    raise NotImplementedError("Copy from build_houston_hiring.py")


def load_histogram_data():
    """Load population histogram rows."""
    raise NotImplementedError("Copy from build_houston_hiring.py")


# ============================================================================
# CANDIDATE-SPECIFIC CONTENT
# ============================================================================

# === Recommendation badge + Signature Pattern ===
SIGNATURE_PATTERN = """<TODO: Signature Pattern block. 200-300 words. METHODOLOGY rules.>"""

# === Three-Axes cards (Talent / Judgment / Skills) — METHODOLOGY 11e word limits ===
TALENT_CARD_HTML   = """<TODO: <=200 words, three-lens read.>"""
JUDGMENT_CARD_HTML = """<TODO: <=200 words, anchored on L1 #8 + sub-L2s.>"""
SKILLS_CARD_HTML   = """<TODO: <=120 words, domain creds + Wiring-Fit pointer.>"""

# === Hard-to-Learn radar dimensions (METHODOLOGY rules) ===
HTL_DIMENSIONS_HTML = """<TODO: 5-dim radar HTML.>"""

# === Targeted Concerns + Role-Fit (Standards-beat-the-interview framing) ===
CONCERNS_HTML  = """<TODO: 3-5 concern cards, no 'validate whether' framing.>"""
ROLE_FIT_HTML  = """<TODO: What Will Be Easy / What Will Be Hard, seat-responsive.>"""

# === Interview Probes (10 cards) ===
PROBES_HTML = """<TODO: 10 probe cards. Use 'surface' framing, not 'validate'.>"""

# === Wiring-Fit panel ===
WIRING_FIT_HTML = """<TODO: full Wiring-Fit panel HTML.>"""

# === Career Timeline + Awards/Boards/Education ===
CAREER_TIMELINE_HTML = """<TODO>"""
AWARDS_HTML          = """<TODO>"""
BOARD_ROLES_HTML     = """<TODO>"""
EDUCATION_HTML       = """<TODO>"""


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("Loading respondent data...")
    respondent_data = load_respondent_data()

    print("Loading histogram data...")
    zalgo_rows, flag_rows = load_histogram_data()

    print("Building motivators section...")
    # Adapt respondent_data to the motivators_section input shape
    respondent = {
        # TODO: populate from respondent_data
    }
    motivators_html = build_section(respondent, include_css=True)

    print("Loading template...")
    template_html = TEMPLATE.read_text(encoding="utf-8")
    template_html = template_html.replace("{{MOTIVATORS_ANTIMOTIVATORS_SECTION}}", motivators_html)

    replacements = {
        "CANDIDATE_NAME":      CANDIDATE,
        "REPORT_DATE":         REPORT_DATE,
        "RECOMMENDATION_TEXT": RECOMMENDATION,
        "SEAT_TYPE":           SEAT_TYPE,
        "SIGNATURE_PATTERN":   SIGNATURE_PATTERN,
        "TALENT_CARD_HTML":    TALENT_CARD_HTML,
        "JUDGMENT_CARD_HTML":  JUDGMENT_CARD_HTML,
        "SKILLS_CARD_HTML":    SKILLS_CARD_HTML,
        "HTL_DIMENSIONS_HTML": HTL_DIMENSIONS_HTML,
        "CONCERNS_HTML":       CONCERNS_HTML,
        "ROLE_FIT_HTML":       ROLE_FIT_HTML,
        "PROBES_HTML":         PROBES_HTML,
        "WIRING_FIT_HTML":     WIRING_FIT_HTML,
        "CAREER_TIMELINE_HTML": CAREER_TIMELINE_HTML,
        "AWARDS_HTML":         AWARDS_HTML,
        "BOARD_ROLES_HTML":    BOARD_ROLES_HTML,
        "EDUCATION_HTML":      EDUCATION_HTML,
        # TODO: add headline metrics, DISC numbers, distribution-chart tokens, etc.
    }

    html = template_html
    for token, value in replacements.items():
        html = html.replace(f"{{{{{token}}}}}", str(value))

    qa_gate_hiring(html, candidate_name=CANDIDATE)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    print(f"\nSUCCESS: {OUT}")
    print(f"Size: {OUT.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
