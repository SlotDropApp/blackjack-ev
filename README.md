# blackjack-ev

[![validate](https://github.com/SlotDropApp/blackjack-ev/actions/workflows/validate.yml/badge.svg)](https://github.com/SlotDropApp/blackjack-ev/actions/workflows/validate.yml)

Exact expected value for every blackjack decision — 340 situations, solved
by recursion rather than simulated, then checked against a published chart
transcribed by hand.

No dependencies. Python 3.7+. Runs in about a second.

```
python3 blackjack_ev.py     # solve → data/hands-ev.json
python3 validate.py         # compare all 340 cells against a published chart
python3 export_csv.py       # same table as CSV
```

## The result

```
  340 cells compared

     338 identical
       2 documented marginal
       0 unexplained
```

Two independent sources agree on 338 of 340 cells. The solver derives its
answers from the dealer's final-total distribution; the reference chart in
`reference.py` was typed in from published tables and is never generated
from the solver's output. That independence is the whole point — a test
that derives its expected values from the thing being tested is an
expensive way to confirm that a file equals itself.

## The two that disagree

Both are hands where hitting and doubling are worth very nearly the same:

| hand | published chart | this solver | hit | double | margin |
|---|---|---|---|---|---|
| A,2 vs 5 | double | hit | +0.13336 | +0.12595 | 0.00741 |
| A,4 vs 4 | double | hit | +0.05929 | +0.05843 | **0.00086** |

A,4 vs 4 is decided by less than a thousandth of a bet. A printed chart has
to round that to one letter; this prints the number instead. Neither source
is wrong — the question simply has no clean answer at that margin, and
published charts disagree with each other on exactly these cells.

`validate.py` accepts these two explicitly, and only while the margin stays
under 0.01. Any other disagreement, or either of these widening, fails the
run with a non-zero exit code.

## The thing charts don't show you

Every basic strategy chart tells you the decision. Almost none tell you what
the alternatives were worth, so there is no way to tell a decision that wins
by a mile from one that wins by a rounding error.

That column is in `data/hand-ev.csv`, and it explains the hand everyone
argues about:

| hand | stand | hit | margin |
|---|---|---|---|
| 16 vs 10 | −0.54043 | −0.53983 | 0.0006 |

Hitting 16 against a ten is correct, and it is correct by six ten-thousandths
of a bet. It feels wrong because it very nearly is. Meanwhile 11 vs 6 wins by
0.33 — a five-hundred-fold difference in how much the decision matters,
invisible on any chart that prints one letter per cell.

## Rules modelled

- multi-deck shoe, approximated as an infinite deck
- dealer **stands** on soft 17 (S17)
- blackjack pays 3:2, dealer **peeks** for blackjack
- double on any first two cards, **double after split** allowed (DAS)
- no surrender, one split only (no resplitting)

Change any of these and cells move. Three are notoriously rule-sensitive:
11 vs A, A,7 vs 2, A,8 vs 6 — all three flip between S17 and H17.

The dealer's peek matters more than it looks. When the upcard is an ace or a
ten, hands where the dealer already has blackjack are resolved before the
player acts, so they are excluded and the remaining probabilities
renormalised. Skipping that step is the most common way to get these numbers
slightly wrong, and it pushes every EV against an ace or a ten too low.

### On the infinite deck

Each card is drawn at its nominal probability — 1/13, and 4/13 for the tens —
without removing visible cards from the shoe. This is the convention
published EV tables use. The gap against a real six-deck shoe is on the order
of a thousandth of a bet, below the precision anything here reports.

It is stated rather than hidden because it is what makes the output
reproducible by someone else.

## Data

| file | what |
|---|---|
| `data/hands-ev.json` | 340 situations, every option's EV, the margin, bust probabilities |
| `data/hand-ev.csv` | the same, one row per situation |
| `data/basic-strategy.csv` | just the chart, one symbol per cell |

Each entry:

```json
"16-vs-10": {
  "best": "hit",
  "best_ev": -0.53983,
  "second": "stand",
  "cout_erreur": 0.0006,
  "ev": { "stand": -0.54043, "hit": -0.53983, "double": -1.07965 },
  "p_crever_joueur": 0.61538,
  "p_crever_croupier": 0.22978
}
```

Dealer bust rate by upcard, as a by-product:

```
2:35.4%  3:37.4%  4:39.4%  5:41.6%  6:42.3%
7:26.2%  8:24.5%  9:22.8%  10:23.0%  A:16.7%
```

## Files

```
blackjack_ev.py    the solver — dealer distribution, then player options
reference.py       published basic strategy, transcribed by hand
validate.py        compares the two, exits non-zero on any surprise
export_csv.py      JSON → CSV
```

## What this is not

Not a card counter, not a betting system, and not an edge. Basic strategy
takes the house edge down to roughly half a percent under these rules; it
does not remove it. Played perfectly, forever, you lose slowly.

If a tool ever tells you otherwise, check its margin column.

## Licence

MIT. Use the data, fork the solver, publish your own numbers.

Built for [slotdropapp.com](https://slotdropapp.com), which uses this table
to explain individual hands.
