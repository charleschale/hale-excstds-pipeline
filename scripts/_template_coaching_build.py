"""TEMPLATE: Excellence Standards Coaching Guide build script.

Fork this for the next coaching-guide build. The candidate-specific narrative
content lives in the `# === CANDIDATE-SPECIFIC ===` blocks below; everything
else (data loading, motivators section, qa_gate) is inherited from shared
modules.

Source-of-truth references:
- Card structural rules:   METHODOLOGY.md "Coaching-guide practice-fuel"
- L2 tag color rules:      METHODOLOGY.md "Coaching-guide L2 color tags"
- qa_gate enforcement:     pipeline.qa_gate.qa_gate_coaching()
- Print-CSS contract:      _print_css.json (consumed by render script)
- Brand-lockup discipline: METHODOLOGY.md "Brand-lockup discipline"
- Signature Pattern:       METHODOLOGY.md "Signature Pattern block"

Run from repo root:
    python _pipeline/scripts/build_<slug>_coaching.py
"""
import json
import re
import sys
from pathlib import Path
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "_pipeline" / "src"))

from pipeline.motivators_section import build_section, compute_intensity_from_disc
from pipeline.qa_gate import qa_gate_coaching

# =================== EDIT THESE FOR EACH NEW BUILD ===================
SLUG          = "TODO_lastname_firstname"          # e.g. "Bender_Jody"
CANDIDATE     = "TODO First Last"                  # e.g. "Jody Bender"
CANDIDATE_FN  = "TODO First"                       # e.g. "Jody"
RESPONDENT_ID = "TODO_email_or_id"                  # respondent folder under _respondents/
REPORT_DATE   = "TODO Month DD, YYYY"
CANDIDATE_CREDS = "TODO Title &middot; Company"
CANDIDATE_ROLE  = "TODO Function &middot; Industry &middot; team-size description"
# =====================================================================

RESPONDENT_XLSX = ROOT / "_respondents" / RESPONDENT_ID / "data.xlsx"
HISTOGRAM_XLSX  = ROOT / "Histogram Data.xlsx"
TEMPLATE        = ROOT / "_templates" / "coaching_guide_TEMPLATE.html"
OUT_DIR         = ROOT / "_reports"
OUT             = OUT_DIR / f"{SLUG}_coaching_guide.html"


# ============================================================================
# DATA LOADING (copy boilerplate from build_bender_coaching.py)
# ============================================================================

def load_respondent_data():
    """Load L1, L2, and metadata from the respondent xlsx. Returns a dict.

    See build_bender_coaching.py:load_respondent_data for the canonical impl.
    The returned dict must include: l1_data, l2_data, z_algo_overall,
    z_human_overall, rf_num, flags_lit, disc (Natural + Adapted), DF clusters.
    """
    raise NotImplementedError("Copy from build_bender_coaching.py and adjust as needed")


def load_histogram_data():
    """Load population histogram rows (zalgo + flag bins). See bender build."""
    raise NotImplementedError("Copy from build_bender_coaching.py")


def build_distribution_tokens(zalgo_rows, flag_rows, z_algo, z_human, rf_num):
    """Compute the {{DIST_*}} chart tokens. See bender build."""
    raise NotImplementedError("Copy from build_bender_coaching.py")


def build_respondent_dict(d):
    """Adapter from raw respondent_data to motivators_section.build_section input."""
    raise NotImplementedError("Copy from build_bender_coaching.py")


def build_excstds_scorecard(d):
    """Build the Excellence Standards Dimensional Scorecard tokens."""
    raise NotImplementedError("Copy from build_bender_coaching.py")


# ============================================================================
# CANDIDATE-SPECIFIC CONTENT
# ============================================================================

# === Signature Pattern (200-300 words, METHODOLOGY rules apply) ===
SIGNATURE_PATTERN = """<TODO: Signature Pattern block. See METHODOLOGY 'Signature Pattern block'.>"""

# === Behavioral Fingerprint narrative (~3 paragraphs) ===
FINGERPRINT_NARRATIVE = """<TODO: 3-paragraph behavioral fingerprint anchored on TTI wheel position.>"""

# === Driving Forces blocks ===
DRIVING_FORCES_PRIMARY_HTML       = """<TODO: Primary DF cluster paragraph.>"""
DRIVING_FORCES_INDIFFERENT_HTML   = """<TODO: Indifferent DF cluster paragraph.>"""
DRIVING_FORCES_IMPLICATIONS_HTML  = """<TODO: 3 implications for the seat.>"""

# === DISC notes ===
DISC_NOTE_TEXT       = """<TODO short>"""
DISC_NOTE_DETAIL     = """<TODO long>"""
DISC_ANNOTATION_CODE = """// TODO: chart annotation customizations if any"""

# === Wiring-Fit items ===
WIRING_FIT_ITEMS = """<TODO: Wiring-Fit table HTML rows.>"""


# ============================================================================
# IMPACT ITEMS — flag-driven (>=3) + per-answer (>=9)
# ============================================================================

def build_impact_items_html():
    """Return the HTML for Part 2: Flag-Driven Items + Per-Answer Impact Items.

    Card structure (each Impact card MUST follow this shape — see METHODOLOGY):

        <div class="practice-item flag-driven">                          <!-- or just "practice-item" -->
          <div style="display:flex; align-items:baseline; gap:12px;">
            <span class="practice-num">N</span>
            <div style="flex:1;">
              <div class="practice-item-title">...</div>
              <div class="practice-qref">Q### &middot; Dimension &middot; you answered X; the standard is Y</div>
            </div>
            <div class="practice-l2-tag" style="background:#XXX; color:#YYY; border-color:#ZZZ;" data-l2="X.Y">X.Y NAME</div>
          </div>
          <div class="practice-body">
            <p>...</p>
          </div>
          <div class="practice-fuel">Routine: ...</div>
        </div>
    """
    flag_subheader = (
        '<div class="practice-subsection-hdr">'
        '<div class="practice-subsection-hdr-title">Flag-Driven Items</div>'
        '<div class="practice-subsection-hdr-blurb">Lit flags from the cohort research &mdash; '
        'pattern-level effectiveness levers that sit across multiple L1s. Addressed before per-answer lifts.</div>'
        '</div>'
    )
    flag_cards = []  # TODO: append at least 3 flag-driven cards using the structure above

    peranswer_subheader = (
        '<div class="practice-subsection-hdr">'
        '<div class="practice-subsection-hdr-title">Per-Answer Impact Items</div>'
        '<div class="practice-subsection-hdr-blurb">Specific question-level lifts ranked by impact. '
        'Each one is a single-L2 effectiveness lever that compounds when paired with the flag-driven items above.</div>'
        '</div>'
    )
    impact_cards = []  # TODO: append at least 9 per-answer impact cards

    return flag_subheader + "\n".join(flag_cards) + peranswer_subheader + "\n".join(impact_cards)


def build_teach_items_html():
    """Return the HTML for Part 1: Teach Items (>=10 cards).

    Each Teach card MUST follow the same structural rules as Impact cards.
    Practice-fuel content for Teach cards begins with "Routine to protect:".
    """
    teach_subheader = (
        '<div class="practice-subsection-hdr">'
        '<div class="practice-subsection-hdr-title">Teach Items</div>'
        '<div class="practice-subsection-hdr-blurb">Standards you answered correctly. '
        'These are the muscles already in place &mdash; worth naming explicitly because the work ahead '
        'depends on protecting them as the seat scales.</div>'
        '</div>'
    )
    teach_cards = []  # TODO: append at least 10 teach cards

    return teach_subheader + "\n".join(teach_cards)


# ============================================================================
# CONNECTION + CLOSING
# ============================================================================

CONNECTION_NARRATIVE_HTML = """<TODO: How the Two Lines Connect — integrative read.>"""

CAREER_TIMELINE_TITLE = f"Career Timeline &mdash; {CANDIDATE}"
CAREER_TIMELINE_HTML  = """<TODO: Career timeline blocks.>"""

CLOSING_NOTE_HTML = """<TODO: One closing paragraph + 3 things-to-come-back-to.>"""


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("Loading respondent data...")
    respondent_data = load_respondent_data()

    print("Loading histogram data...")
    zalgo_rows, flag_rows = load_histogram_data()

    print("Building distribution chart tokens...")
    dist_tokens = build_distribution_tokens(
        zalgo_rows, flag_rows,
        respondent_data["z_algo_overall"],
        respondent_data["z_human_overall"],
        respondent_data["rf_num"],
    )

    print("Building motivators section...")
    respondent = build_respondent_dict(respondent_data)
    motivators_html = build_section(respondent, include_css=True)

    print("Building scorecard...")
    scorecard = build_excstds_scorecard(respondent_data)

    print("Building impact / teach items...")
    impact_html = build_impact_items_html()
    teach_html  = build_teach_items_html()

    print("Loading template...")
    template_html = TEMPLATE.read_text(encoding="utf-8")

    # Inject motivators (raw braces — must precede token replace loop)
    template_html = template_html.replace("{{MOTIVATORS_ANTIMOTIVATORS_SECTION}}", motivators_html)

    replacements = {
        # Header / meta
        "CANDIDATE_NAME":  CANDIDATE,
        "CANDIDATE_CREDS": CANDIDATE_CREDS,
        "CANDIDATE_ROLE":  CANDIDATE_ROLE,
        "REPORT_DATE":     REPORT_DATE,

        # Narrative blocks
        "SIGNATURE_PATTERN":                SIGNATURE_PATTERN,
        "FINGERPRINT_NARRATIVE":            FINGERPRINT_NARRATIVE,
        "DRIVING_FORCES_PRIMARY_HTML":      DRIVING_FORCES_PRIMARY_HTML,
        "DRIVING_FORCES_INDIFFERENT_HTML":  DRIVING_FORCES_INDIFFERENT_HTML,
        "DRIVING_FORCES_IMPLICATIONS_HTML": DRIVING_FORCES_IMPLICATIONS_HTML,

        # Headline metrics — populate from respondent_data
        "ZALGO_OVERALL":  f"{respondent_data['z_algo_overall']:+.2f}",
        "COHORT_AVG":     "+0.24",
        "TEACH_ITEMS":    "10/10",
        "IMPACT_ITEMS":   "TODO",
        "FLAGS_LIT":      str(len(respondent_data["flags_lit"])),
        "REVERSE_FLAGS":  str(respondent_data["rf_num"]),

        # DISC numbers — fill from respondent_data["disc"]
        "DISC_D_NAT": "TODO", "DISC_I_NAT": "TODO", "DISC_S_NAT": "TODO", "DISC_C_NAT": "TODO",
        "DISC_D_ADP": "TODO", "DISC_I_ADP": "TODO", "DISC_S_ADP": "TODO", "DISC_C_ADP": "TODO",
        "DISC_NOTE_TEXT":         DISC_NOTE_TEXT,
        "DISC_NOTE_DETAIL":       DISC_NOTE_DETAIL,
        "DISC_ANNOTATION_CODE":   DISC_ANNOTATION_CODE,

        # Wiring-Fit
        "WIRING_FIT_ITEMS": WIRING_FIT_ITEMS,

        # Excellence Standards scorecard
        **scorecard,

        # Distribution charts
        **dist_tokens,

        # Teach & Impact
        "TEACH_ITEMS_HTML":  teach_html,
        "IMPACT_ITEMS_HTML": impact_html,

        # Connection / timeline / closing
        "CONNECTION_NARRATIVE_HTML": CONNECTION_NARRATIVE_HTML,
        "CAREER_TIMELINE_TITLE":     CAREER_TIMELINE_TITLE,
        "CAREER_TIMELINE_HTML":      CAREER_TIMELINE_HTML,
        "CLOSING_NOTE_HTML":         CLOSING_NOTE_HTML,
    }

    html = template_html
    for token, value in replacements.items():
        html = html.replace(f"{{{{{token}}}}}", str(value))

    # === QA GATE — runs the full S11g + S11h + structural-balance contract ===
    qa_gate_coaching(html, candidate_name=CANDIDATE)

    # Write output
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    print(f"\nSUCCESS: {OUT}")
    print(f"Size: {OUT.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
