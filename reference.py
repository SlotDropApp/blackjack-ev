# -*- coding: utf-8 -*-
"""
Published basic strategy, transcribed by hand. The control source.

This file must NEVER be generated from the solver's output. Its only
purpose is to be independent of it, so that validate.py compares two
things that cannot share the same mistake. A check that derives its
expected values from the thing being checked proves nothing — it is a
very expensive way of confirming that a file equals itself.

Transcribed from the standard multi-deck chart: dealer stands on soft 17
(S17), dealer peeks, double after split allowed (DAS), no resplitting,
no surrender.

Column order: dealer shows 2 3 4 5 6 7 8 9 10 A

    H   hit
    S   stand
    D   double, hit if doubling is not allowed
    Ds  double, stand if doubling is not allowed
    P   split

Three cells flip when the ruleset changes, and they are the classic
traps: 11 vs A (hit under S17, double under H17), A,7 vs 2 (stand under
S17), A,8 vs 6 (stand under S17, double under H17). If you adapt this to
another ruleset, start there.
"""

REFERENCE = {
    # ── hard totals ────────────────────────────────────────────────
    "5":  ["H", "H", "H", "H", "H", "H", "H", "H", "H", "H"],
    "6":  ["H", "H", "H", "H", "H", "H", "H", "H", "H", "H"],
    "7":  ["H", "H", "H", "H", "H", "H", "H", "H", "H", "H"],
    "8":  ["H", "H", "H", "H", "H", "H", "H", "H", "H", "H"],
    "9":  ["H", "D", "D", "D", "D", "H", "H", "H", "H", "H"],
    "10": ["D", "D", "D", "D", "D", "D", "D", "D", "H", "H"],
    "11": ["D", "D", "D", "D", "D", "D", "D", "D", "D", "H"],
    "12": ["H", "H", "S", "S", "S", "H", "H", "H", "H", "H"],
    "13": ["S", "S", "S", "S", "S", "H", "H", "H", "H", "H"],
    "14": ["S", "S", "S", "S", "S", "H", "H", "H", "H", "H"],
    "15": ["S", "S", "S", "S", "S", "H", "H", "H", "H", "H"],
    "16": ["S", "S", "S", "S", "S", "H", "H", "H", "H", "H"],
    "17": ["S", "S", "S", "S", "S", "S", "S", "S", "S", "S"],
    "18": ["S", "S", "S", "S", "S", "S", "S", "S", "S", "S"],
    "19": ["S", "S", "S", "S", "S", "S", "S", "S", "S", "S"],
    "20": ["S", "S", "S", "S", "S", "S", "S", "S", "S", "S"],

    # ── soft totals ────────────────────────────────────────────────
    "soft-13": ["H", "H", "H", "D",  "D",  "H", "H", "H", "H", "H"],
    "soft-14": ["H", "H", "H", "D",  "D",  "H", "H", "H", "H", "H"],
    "soft-15": ["H", "H", "D", "D",  "D",  "H", "H", "H", "H", "H"],
    "soft-16": ["H", "H", "D", "D",  "D",  "H", "H", "H", "H", "H"],
    "soft-17": ["H", "D", "D", "D",  "D",  "H", "H", "H", "H", "H"],
    "soft-18": ["S", "Ds", "Ds", "Ds", "Ds", "S", "S", "H", "H", "H"],
    "soft-19": ["S", "S", "S", "S",  "S",  "S", "S", "S", "S", "S"],
    "soft-20": ["S", "S", "S", "S",  "S",  "S", "S", "S", "S", "S"],

    # ── pairs ──────────────────────────────────────────────────────
    "pair-2s":   ["P", "P", "P", "P", "P", "P", "H", "H", "H", "H"],
    "pair-3s":   ["P", "P", "P", "P", "P", "P", "H", "H", "H", "H"],
    "pair-4s":   ["H", "H", "H", "P", "P", "H", "H", "H", "H", "H"],
    "pair-5s":   ["D", "D", "D", "D", "D", "D", "D", "D", "H", "H"],
    "pair-6s":   ["P", "P", "P", "P", "P", "H", "H", "H", "H", "H"],
    "pair-7s":   ["P", "P", "P", "P", "P", "P", "H", "H", "H", "H"],
    "pair-8s":   ["P", "P", "P", "P", "P", "P", "P", "P", "P", "P"],
    "pair-9s":   ["P", "P", "P", "P", "P", "S", "P", "P", "S", "S"],
    "pair-10s":  ["S", "S", "S", "S", "S", "S", "S", "S", "S", "S"],
    "pair-aces": ["P", "P", "P", "P", "P", "P", "P", "P", "P", "P"],
}

UPCARDS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "a"]

# The two cells where published charts and this solver disagree, both by
# less than a hundredth of a bet. They are listed here as (published,
# solver) so that validate.py can accept them explicitly rather than
# silently — and only while the margin stays under MARGIN_THRESHOLD. If a
# future change widens the gap, the check fails and asks for a human.
#
# Not a fudge factor: any other disagreement, and any of these two growing
# past the threshold, still fails the run.
KNOWN_MARGINAL = {
    "soft-13-vs-5": ("D", "H"),
    "soft-15-vs-4": ("D", "H"),
}
MARGIN_THRESHOLD = 0.01
