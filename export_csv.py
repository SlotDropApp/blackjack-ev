#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Write the solved table as CSV, for people who would rather not parse JSON.

    python3 export_csv.py

Produces two files:

    data/basic-strategy.csv   the chart — one row per hand, one column
                              per dealer upcard, one symbol per cell
    data/hand-ev.csv          the numbers — one row per situation, with
                              the expected value of every option

The second is the one worth having. Every published basic strategy chart
shows you the decision; almost none show you what the alternatives were
worth, so there is no way to tell a decision that wins by a mile from one
that wins by a thousandth. The margin column is that distinction, and it
is why 16 vs 10 feels wrong to everyone who plays it — hitting beats
standing there by 0.0006 of a bet.

CSV is written with a plain comma and no locale formatting, so it opens
the same way everywhere.
"""
import csv
import json
import os
import sys

from reference import REFERENCE, UPCARDS
from validate import code

BASE = os.path.dirname(os.path.abspath(__file__))
HEADERS = [u.upper() for u in UPCARDS]


def load():
    path = os.path.join(BASE, "data", "hands-ev.json")
    if not os.path.exists(path):
        sys.exit("data/hands-ev.json not found — run: python3 blackjack_ev.py")
    return json.load(open(path, encoding="utf-8"))


def chart(table, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["hand"] + HEADERS)
        for hand in REFERENCE:
            w.writerow([hand] + [code(table["%s-vs-%s" % (hand, u)]) for u in UPCARDS])


def values(table, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["hand", "dealer_upcard", "best_action", "best_ev",
                    "second_action", "margin",
                    "ev_stand", "ev_hit", "ev_double", "ev_split",
                    "p_player_busts_on_next_card", "p_dealer_busts"])
        for hand in REFERENCE:
            for u in UPCARDS:
                e = table["%s-vs-%s" % (hand, u)]
                ev = e["ev"]
                w.writerow([
                    hand, u.upper(), e["best"], e["best_ev"],
                    e["second"], e["cout_erreur"],
                    ev.get("stand", ""), ev.get("hit", ""),
                    ev.get("double", ""), ev.get("split", ""),
                    e["p_crever_joueur"], e["p_crever_croupier"],
                ])


def main():
    table = load()
    d = os.path.join(BASE, "data")
    os.makedirs(d, exist_ok=True)

    a = os.path.join(d, "basic-strategy.csv")
    b = os.path.join(d, "hand-ev.csv")
    chart(table, a)
    values(table, b)

    for p in (a, b):
        rows = sum(1 for _ in open(p, encoding="utf-8")) - 1
        print("  %-28s %3d rows, %.1f KB"
              % ("data/" + os.path.basename(p), rows, os.path.getsize(p) / 1024))
    return 0


if __name__ == "__main__":
    sys.exit(main())
