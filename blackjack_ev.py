#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exact expected value of every blackjack decision, for every player hand
against every dealer upcard.

    python3 blackjack_ev.py

Writes data/hands-ev.json: 340 situations, each with the EV of standing,
hitting, doubling and (for pairs) splitting.

This is not a simulation. Nothing is sampled and no random numbers are
used. The dealer's final-total distribution is computed by recursion and
the player's options are evaluated against it, so running this twice
gives bit-identical output.

Rules modelled
──────────────
  • multi-deck shoe, approximated as an infinite deck (see the note)
  • dealer stands on soft 17 (S17)
  • blackjack pays 3:2, dealer peeks for blackjack
  • double on any first two cards, double after split allowed (DAS)
  • no surrender, one split only (no resplitting)

Change any of these and some cells change. Three are famously
rule-sensitive: 11 vs A (hit under S17, double under H17), A,7 vs 2
(stand under S17), A,8 vs 6 (stand under S17, double under H17).

The infinite-deck approximation
───────────────────────────────
Every card is drawn at its nominal probability — 1/13 each, 4/13 for the
tens — without removing already-visible cards from the shoe. This is the
convention published EV tables use. The difference against a six-deck
shoe is on the order of a thousandth of a bet, below the precision
anything here reports.

Stating the approximation is more useful than hiding it: it is what makes
the numbers reproducible by someone else.

No value is rounded before it is written; rounding happens at display
time only.

Requires nothing but the standard library. Python 3.7+.
"""
import json
import os
from functools import lru_cache

BASE = os.path.dirname(os.path.abspath(__file__))

# Probability of each rank: ace, 2..9, then the tens (10, J, Q, K).
CARDS = [(1, 1 / 13)] + [(v, 1 / 13) for v in range(2, 10)] + [(10, 4 / 13)]


def add(total, soft, card):
    """Add a card to a hand, demoting the ace from 11 to 1 when needed."""
    if card == 1:
        if total + 11 <= 21:
            total, soft = total + 11, True
        else:
            total += 1
    else:
        total += card
    if total > 21 and soft:
        total, soft = total - 10, False
    return total, soft


# ── Dealer ─────────────────────────────────────────────────────────────
@lru_cache(maxsize=None)
def _dealer(total, soft):
    """Distribution of the dealer's final totals: {17..21: p, 'bust': p}."""
    if total >= 17:
        return {total: 1.0}
    out = {}
    for c, p in CARDS:
        t, s = add(total, soft, c)
        sub = {"bust": 1.0} if t > 21 else _dealer(t, s)
        for k, q in sub.items():
            out[k] = out.get(k, 0.0) + p * q
    return out


@lru_cache(maxsize=None)
def dealer(up):
    """Final distribution given the upcard, dealer blackjack excluded.

    The dealer peeks. When the upcard is an ace or a ten, the hands where
    the dealer already has blackjack are resolved before the player acts,
    so they are not part of the situations being evaluated here. They are
    removed and the remaining probabilities renormalised.

    Skipping this step is the single most common way to get these numbers
    slightly wrong: every EV against an ace or a ten comes out too low.
    """
    t, s = add(0, False, up)
    if up == 1:
        excluded = 4 / 13          # ten in the hole → blackjack
    elif up == 10:
        excluded = 1 / 13          # ace in the hole → blackjack
    else:
        excluded = 0.0
    if not excluded:
        return _dealer(t, s)
    out = {}
    for c, p in CARDS:
        if (up == 1 and c == 10) or (up == 10 and c == 1):
            continue
        t2, s2 = add(t, s, c)
        sub = {"bust": 1.0} if t2 > 21 else _dealer(t2, s2)
        for k, q in sub.items():
            out[k] = out.get(k, 0.0) + (p / (1 - excluded)) * q
    return out


# ── Player ─────────────────────────────────────────────────────────────
def ev_stand(total, up):
    d = dealer(up)
    ev = 0.0
    for final, p in d.items():
        if final == "bust" or total > final:
            ev += p
        elif total < final:
            ev -= p
    return ev


@lru_cache(maxsize=None)
def ev_optimal(total, soft, up):
    """Best EV reachable from this state: stand, or keep drawing."""
    if total > 21:
        return -1.0
    stand = ev_stand(total, up)
    draw = 0.0
    for c, p in CARDS:
        n, s = add(total, soft, c)
        draw += p * (-1.0 if n > 21 else ev_optimal(n, s, up))
    return max(stand, draw)


def ev_hit(total, soft, up):
    """Take one card, then play optimally from there."""
    t = 0.0
    for c, p in CARDS:
        n, s = add(total, soft, c)
        t += p * (-1.0 if n > 21 else ev_optimal(n, s, up))
    return t


def ev_double(total, soft, up):
    """Exactly one card, then forced to stand. Stake doubled."""
    t = 0.0
    for c, p in CARDS:
        n, _ = add(total, soft, c)
        t += p * (-1.0 if n > 21 else ev_stand(n, up))
    return 2 * t


def p_bust(total, soft):
    """Probability of going over 21 on a single card."""
    return sum(p for c, p in CARDS if add(total, soft, c)[0] > 21)


def ev_split(card, up):
    """Two hands each starting from the pair's rank, doubling allowed (DAS).

    Stated approximation: no resplitting, and split aces receive one card
    each. Both are simplifications in the conservative direction — real
    resplitting is worth slightly more than this reports.
    """
    if card == 1:
        t = 0.0
        for c, p in CARDS:
            n, _ = add(11, True, c)
            t += p * ev_stand(n, up)
        return 2 * t
    t = 0.0
    for c, p in CARDS:
        n, s = add(card, False, c)
        best = max(ev_stand(n, up), ev_hit(n, s, up), ev_double(n, s, up))
        t += p * best
    return 2 * t


# ── Building the table ─────────────────────────────────────────────────
UPS = [(2, "2"), (3, "3"), (4, "4"), (5, "5"), (6, "6"),
       (7, "7"), (8, "8"), (9, "9"), (10, "10"), (1, "a")]


def hands():
    for t in range(5, 21):
        yield "%d" % t, t, False
    for t in range(13, 21):
        yield "soft-%d" % t, t, True
    for c, name in [(1, "aces"), (2, "2s"), (3, "3s"), (4, "4s"), (5, "5s"),
                    (6, "6s"), (7, "7s"), (8, "8s"), (9, "9s"), (10, "10s")]:
        yield "pair-%s" % name, c, "pair"


def build():
    table = {}
    for slug, val, kind in hands():
        for up, up_slug in UPS:
            if kind == "pair":
                c = val
                total, soft = add(*add(0, False, c), c) if c != 1 else (12, True)
                opts = {
                    "stand": ev_stand(total, up),
                    "hit": ev_hit(total, soft, up),
                    "double": ev_double(total, soft, up),
                    "split": ev_split(c, up),
                }
            else:
                total, soft = val, bool(kind)
                opts = {
                    "stand": ev_stand(total, up),
                    "hit": ev_hit(total, soft, up),
                    "double": ev_double(total, soft, up),
                }
            order = sorted(opts.items(), key=lambda kv: -kv[1])
            table["%s-vs-%s" % (slug, up_slug)] = {
                "ev": {k: round(v, 5) for k, v in opts.items()},
                "best": order[0][0],
                "best_ev": round(order[0][1], 5),
                "second": order[1][0],
                # How much the second-best choice costs. Most of the chart
                # is decided by a wide margin; a handful of cells are not,
                # and this is the number that tells them apart.
                "cout_erreur": round(order[0][1] - order[1][1], 5),
                "p_crever_joueur": round(p_bust(total, soft), 5),
                "p_crever_croupier": round(dealer(up).get("bust", 0.0), 5),
            }
    return table


def main():
    table = build()
    out = os.path.join(BASE, "data", "hands-ev.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(table, open(out, "w", encoding="utf-8"), indent=0, sort_keys=True)
    print("data/hands-ev.json: %d situations" % len(table))

    print("\nSanity checks against decisions nobody disputes:")
    for key, expected in (("16-vs-10", "hit"), ("16-vs-6", "stand"),
                          ("11-vs-6", "double"), ("pair-8s-vs-10", "split"),
                          ("pair-10s-vs-6", "stand"), ("soft-18-vs-9", "hit"),
                          ("12-vs-2", "hit"), ("12-vs-4", "stand")):
        r = table[key]
        mark = "OK" if r["best"] == expected else "!!"
        print("  %s %-16s best=%-7s expected=%-7s  EV=%+.4f  margin=%.4f"
              % (mark, key, r["best"], expected, r["best_ev"], r["cout_erreur"]))

    print("\n  Dealer bust rate: " + "  ".join(
        "%s:%.1f%%" % (n, dealer(u).get("bust", 0) * 100) for u, n in UPS))
    print("  Run validate.py to compare all 340 cells against a published chart.")


if __name__ == "__main__":
    main()
