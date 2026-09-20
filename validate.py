#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compare all 340 solved cells against a hand-transcribed published chart.

    python3 validate.py            summary
    python3 validate.py --all      print the full grid

Exit code 0 if the two agree everywhere except the documented marginal
cells; 1 otherwise. Suitable for CI.

Why this exists
───────────────
A solver that is wrong is worse than no solver, because it is wrong with
decimals attached. The only cheap defence is a second source that does
not share its assumptions — here, a chart transcribed by hand from
published tables in reference.py.

The two are genuinely independent. The solver derives its answers from
the dealer's final-total distribution; the reference is typed in from a
book. If they agree on 338 of 340 cells, either both are right or both
are wrong in exactly the same way, and the second is unlikely.

What counts as agreement
────────────────────────
D and Ds are compared as the same decision. They differ only in the
fallback when the house forbids doubling, which is a table rule and not
a property of the hand; the solver records that fallback separately, in
the "second" field.
"""
import json
import os
import sys

from reference import REFERENCE, UPCARDS, KNOWN_MARGINAL, MARGIN_THRESHOLD

BASE = os.path.dirname(os.path.abspath(__file__))
FULL = "--all" in sys.argv

LABEL = {"H": "hit", "S": "stand", "D": "double", "Ds": "double", "P": "split"}


def code(entry):
    """The solver's answer as a chart symbol."""
    best = entry["best"]
    if best == "split":
        return "P"
    if best == "stand":
        return "S"
    if best == "hit":
        return "H"
    # Ds vs D: which way to fall back when doubling is refused. Read from
    # the solver's second-best action, not decided here.
    return "Ds" if entry.get("second") == "stand" else "D"


def load():
    path = os.path.join(BASE, "data", "hands-ev.json")
    if not os.path.exists(path):
        sys.exit("data/hands-ev.json not found — run: python3 blackjack_ev.py")
    return json.load(open(path, encoding="utf-8"))


def main():
    table = load()
    same, marginal, wrong = 0, [], []

    for hand, row in REFERENCE.items():
        for i, published in enumerate(row):
            key = "%s-vs-%s" % (hand, UPCARDS[i])
            entry = table.get(key)
            if entry is None:
                wrong.append((key, published, "—", 0.0, "missing from solver output"))
                continue
            solved = code(entry)

            if LABEL[published] == LABEL[solved]:
                same += 1
                continue

            margin = entry["cout_erreur"]
            expected = KNOWN_MARGINAL.get(key)
            if expected == (published, solved) and margin < MARGIN_THRESHOLD:
                marginal.append((key, published, solved, margin, entry["ev"]))
            else:
                why = ("margin %.5f exceeds the %.2f threshold" % (margin, MARGIN_THRESHOLD)
                       if expected else "not a documented divergence")
                wrong.append((key, published, solved, margin, why))

    total = sum(len(r) for r in REFERENCE.values())
    print("\n  %d cells compared\n" % total)
    print("     %3d identical" % same)
    print("     %3d documented marginal" % len(marginal))
    print("     %3d unexplained" % len(wrong))

    if marginal:
        print("\n  Marginal cells — published chart and solver disagree, by a")
        print("  margin smaller than the rounding on most printed charts:\n")
        for key, published, solved, margin, ev in marginal:
            print("     %-16s chart says %-3s   solver says %-3s   margin %.5f"
                  % (key, published, solved, margin))
            for action, v in sorted(ev.items(), key=lambda kv: -kv[1])[:2]:
                print("          %-8s %+.5f" % (action, v))
        print("\n  Both are hands where hitting and doubling are worth almost")
        print("  exactly the same. Published charts round to a single symbol;")
        print("  this prints the number instead. Neither is a mistake.")

    if wrong:
        print("\n  ✗ Unexplained disagreements:\n")
        for key, published, solved, margin, why in wrong:
            print("     %-16s chart %-3s  solver %-3s  margin %.5f  — %s"
                  % (key, published, solved, margin, why))
        print()
        return 1

    if FULL:
        print("\n  Solver output, chart notation:\n")
        print("     %-11s %s" % ("", "  ".join("%-2s" % u.upper() for u in UPCARDS)))
        for hand in REFERENCE:
            cells = [code(table["%s-vs-%s" % (hand, u)]) for u in UPCARDS]
            print("     %-11s %s" % (hand, "  ".join("%-2s" % c for c in cells)))

    print("\n  ✓ %d identical, %d documented — the solver agrees with published"
          "\n    basic strategy everywhere it is not a coin flip.\n" % (same, len(marginal)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
