#!/usr/bin/env python3
"""
render_distribution.py — Compute population distribution chart tokens for hiring reports.

Reads population_scores.csv (the full N=1088 population export from Power BI),
takes an individual's Key3 identifier, and produces a dict of template tokens
that plug into the hiring_report_TEMPLATE.html distribution charts.

Usage:
    # As a module (called from the rendering pipeline):
    from render_distribution import compute_distribution_tokens
    tokens = compute_distribution_tokens(population_csv, key3)

    # Standalone test:
    python render_distribution.py <population_csv> <key3>
"""
import csv
import json
import math
import sys
from pathlib import Path


# ── Bin definitions (matching Power BI) ──────────────────────────────

# Z-score bins for Charts 1 & 2: half-unit steps from -4.0 to +4.0
Z_BIN_EDGES = [round(-4.0 + i * 0.5, 1) for i in range(17)]  # -4.0 to +4.0

# Flag bins for Chart 3: 5-unit steps from 0 to 50
FLAG_BIN_EDGES = list(range(0, 55, 5))  # 0, 5, 10, ..., 50


def _load_population(csv_path):
    """Load population_scores.csv into a list of dicts with typed values."""
    rows = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            row = {
                "Key3": r["Key3"],
                "SuccessFlag": r["SuccessFlag"],
                "ZAlgo": float(r["@Z|Algo"]) if r["@Z|Algo"] else None,
                "ZHuman": float(r["@Z|Human"]) if r["@Z|Human"] else None,
                "RF": int(float(r["@#RF"])) if r["@#RF"] else None,
            }
            rows.append(row)
    return rows


def _bin_index(value, edges):
    """
    Return the bin index for a value given sorted bin edges.
    Clamps outliers into the first/last bin.
    edges = [e0, e1, e2, ...] defines bins [e0,e1), [e1,e2), ...
    Last bin is [e_{n-2}, e_{n-1}] (inclusive on both sides for the last).
    """
    if value is None:
        return None
    n_bins = len(edges) - 1
    if value <= edges[0]:
        return 0
    if value >= edges[-1]:
        return n_bins - 1
    for i in range(n_bins):
        if edges[i] <= value < edges[i + 1]:
            return i
    return n_bins - 1


def _histogram(values, edges):
    """Count values into bins defined by edges. Returns list of counts."""
    n_bins = len(edges) - 1
    counts = [0] * n_bins
    for v in values:
        idx = _bin_index(v, edges)
        if idx is not None:
            counts[idx] += 1
    return counts


def _make_z_labels(edges):
    """Two-row labels for z-score bins: [["-3.5","-3.0"], ...]"""
    labels = []
    for i in range(len(edges) - 1):
        lo = f"{edges[i]:+.1f}" if edges[i] != 0 else "0.0"
        hi = f"{edges[i+1]:+.1f}" if edges[i+1] != 0 else "0.0"
        # Strip leading + for cleaner display
        lo = lo.lstrip("+") if lo.startswith("+") else lo
        hi = hi.lstrip("+") if hi.startswith("+") else hi
        labels.append([lo, hi])
    return labels


def _make_flag_labels(edges):
    """Two-row labels for flag bins: [["0","5"], ["5","10"], ...]"""
    labels = []
    for i in range(len(edges) - 1):
        labels.append([str(edges[i]), str(edges[i + 1])])
    return labels


def _trim_empty_leading(labels, *count_lists):
    """Remove leading bins where ALL count lists are zero."""
    while labels and all(cl[0] == 0 for cl in count_lists):
        labels.pop(0)
        for cl in count_lists:
            cl.pop(0)


def _trim_empty_trailing(labels, *count_lists):
    """Remove trailing bins where ALL count lists are zero."""
    while labels and all(cl[-1] == 0 for cl in count_lists):
        labels.pop()
        for cl in count_lists:
            cl.pop()


def _omit_empty_bins_sf(labels, fail_counts, success_counts):
    """
    For Success/Fail chart: remove bins where BOTH fail and success are 0.
    Returns new (labels, fail, success) lists.
    Extends edge bins to capture outliers (first bin lower bound = -99,
    last bin upper bound = +99).
    """
    new_labels, new_fail, new_success = [], [], []
    for i in range(len(labels)):
        if fail_counts[i] != 0 or success_counts[i] != 0:
            new_labels.append(labels[i])
            new_fail.append(fail_counts[i])
            new_success.append(success_counts[i])
    # Fix edge labels to show they capture outliers
    if new_labels:
        new_labels[-1] = [new_labels[-1][0], "+"]
    return new_labels, new_fail, new_success


def _find_bin_in_filtered(original_bin_idx, original_labels, filtered_labels):
    """
    After filtering empty bins, find the new index corresponding to
    the original bin index. Returns the new index or 0 if not found.
    """
    if original_bin_idx is None or original_bin_idx >= len(original_labels):
        return 0
    target_label = original_labels[original_bin_idx]
    for i, lbl in enumerate(filtered_labels):
        if lbl[0] == target_label[0]:  # Match on lower bound
            return i
    return 0


def compute_distribution_tokens(csv_path, key3):
    """
    Main entry point. Returns a dict of template tokens for the distribution
    charts section.

    Parameters:
        csv_path: path to population_scores.csv
        key3: the respondent's Key3 identifier (e.g. "20250404.jbender@company.com")

    Returns:
        dict with keys like DIST_ZLABELS, DIST_ALGO_COUNTS, etc.
    """
    pop = _load_population(csv_path)

    # Find the individual
    individual = None
    for row in pop:
        if row["Key3"] == key3:
            individual = row
            break

    if individual is None:
        raise ValueError(f"Key3 '{key3}' not found in population data")

    # ── Chart 1: Full population dual histogram (Z|Algo + Z|Human) ──
    algo_values = [r["ZAlgo"] for r in pop if r["ZAlgo"] is not None]
    human_values = [r["ZHuman"] for r in pop if r["ZHuman"] is not None]

    z_labels = _make_z_labels(Z_BIN_EDGES)
    algo_counts = _histogram(algo_values, Z_BIN_EDGES)
    human_counts = _histogram(human_values, Z_BIN_EDGES)

    # Trim leading/trailing empty bins (where BOTH algo and human are 0)
    _trim_empty_leading(z_labels, algo_counts, human_counts)
    _trim_empty_trailing(z_labels, algo_counts, human_counts)

    j_algo_bin = _bin_index(individual["ZAlgo"], Z_BIN_EDGES)
    j_human_bin = _bin_index(individual["ZHuman"], Z_BIN_EDGES)

    # Adjust bin indices for trimmed leading bins
    # Count how many leading bins were trimmed from the original 16
    original_count = len(Z_BIN_EDGES) - 1
    trimmed_leading = original_count - len(z_labels)
    # Actually, let's recalculate more carefully
    full_z_labels = _make_z_labels(Z_BIN_EDGES)
    full_algo = _histogram(algo_values, Z_BIN_EDGES)
    full_human = _histogram(human_values, Z_BIN_EDGES)

    # Find how many leading bins were removed
    leading_removed = 0
    for i in range(len(full_algo)):
        if full_algo[i] == 0 and full_human[i] == 0:
            leading_removed += 1
        else:
            break

    j_algo_bin_adj = j_algo_bin - leading_removed if j_algo_bin is not None else 0
    j_human_bin_adj = j_human_bin - leading_removed if j_human_bin is not None else 0

    # Clamp to valid range
    j_algo_bin_adj = max(0, min(j_algo_bin_adj, len(z_labels) - 1))
    j_human_bin_adj = max(0, min(j_human_bin_adj, len(z_labels) - 1))

    # ── Chart 2: Success vs Fail cohorts (Z|Algo only) ──
    success_rows = [r for r in pop if str(r["SuccessFlag"]).strip().lower() == "true"]
    fail_rows = [r for r in pop if str(r["SuccessFlag"]).strip().lower() == "false"]

    success_algo = [r["ZAlgo"] for r in success_rows if r["ZAlgo"] is not None]
    fail_algo = [r["ZAlgo"] for r in fail_rows if r["ZAlgo"] is not None]

    sf_z_labels_full = _make_z_labels(Z_BIN_EDGES)
    fail_counts_full = _histogram(fail_algo, Z_BIN_EDGES)
    success_counts_full = _histogram(success_algo, Z_BIN_EDGES)

    # Omit bins where both success and fail are 0
    sf_labels, fail_counts, success_counts = _omit_empty_bins_sf(
        sf_z_labels_full[:], fail_counts_full[:], success_counts_full[:]
    )

    # Find the individual's bin in the filtered set
    sf_algo_orig = _bin_index(individual["ZAlgo"], Z_BIN_EDGES)
    sf_human_orig = _bin_index(individual["ZHuman"], Z_BIN_EDGES)
    sf_algo_bin = _find_bin_in_filtered(sf_algo_orig, sf_z_labels_full, sf_labels)
    sf_human_bin = _find_bin_in_filtered(sf_human_orig, sf_z_labels_full, sf_labels)

    # ── Chart 3: Flag counts ──
    rf_values = [r["RF"] for r in pop if r["RF"] is not None]

    flag_labels = _make_flag_labels(FLAG_BIN_EDGES)
    flag_counts = _histogram(rf_values, FLAG_BIN_EDGES)

    j_flag_bin = _bin_index(individual["RF"], FLAG_BIN_EDGES)
    # Flag chart is natural order (low-left, high-right) — no reversal needed

    # ── Assemble token dict ──
    tokens = {
        # Chart 1: Full population
        "DIST_ZLABELS": json.dumps(z_labels),
        "DIST_ALGO_COUNTS": json.dumps(algo_counts),
        "DIST_HUMAN_COUNTS": json.dumps(human_counts),
        "DIST_JALGO_BIN": str(j_algo_bin_adj),
        "DIST_JHUMAN_BIN": str(j_human_bin_adj),

        # Chart 2: Success / Fail
        "DIST_SF_LABELS": json.dumps(sf_labels),
        "DIST_FAIL_COUNTS": json.dumps(fail_counts),
        "DIST_SUCCESS_COUNTS": json.dumps(success_counts),
        "DIST_SF_ALGO_BIN": str(sf_algo_bin),
        "DIST_SF_HUMAN_BIN": str(sf_human_bin),

        # Chart 3: Flags
        "DIST_FLAG_LABELS": json.dumps(flag_labels),
        "DIST_FLAG_COUNTS": json.dumps(flag_counts),
        "DIST_FLAG_BIN": str(j_flag_bin) if j_flag_bin is not None else "0",
    }

    return tokens


# ── CLI test runner ──────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python render_distribution.py <population_csv> <key3>")
        sys.exit(1)

    csv_path = sys.argv[1]
    key3 = sys.argv[2]

    tokens = compute_distribution_tokens(csv_path, key3)

    print("\n=== Distribution Chart Tokens ===\n")
    for k, v in sorted(tokens.items()):
        # Truncate long arrays for display
        display = v if len(v) < 120 else v[:100] + "..."
        print(f"  {k}: {display}")

    print(f"\n  Total tokens: {len(tokens)}")
