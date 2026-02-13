# ♠ Blackjack Counter

A fast, sleek Hi-Lo card counting assistant for online blackjack.

## Usage

1. Open `index.html` in your browser (just double-click it)
2. Position it next to your online casino window
3. Click or type card ranks as you see them dealt
4. The running count and true count update instantly

## How It Works

**Hi-Lo counting system:**
- Cards 2–6: **+1** (green buttons)
- Cards 7–9: **0** (gray buttons)
- Cards 10, J, Q, K, A: **-1** (red buttons)

**True Count** = Running Count ÷ Decks Remaining

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `2`–`9` | Enter that card |
| `0` | Enter a 10 |
| `J`, `Q`, `K`, `A` | Enter face card / ace |
| `Z` | Undo last card |
| `R` | Reset (new shoe) |
| `N` | Mark new hand |

## Features

- **Rapid input** — click or keyboard, one action per card
- **Color-coded buttons** — instantly see the Hi-Lo value
- **Undo** — fix mistakes with one click
- **Deck tracking** — adjust decks remaining, auto-calculates true count
- **Betting advice** — tells you when to increase/decrease your bet
- **History strip** — see your last 30 cards for verification
- **No install** — pure HTML/CSS/JS, works in any browser