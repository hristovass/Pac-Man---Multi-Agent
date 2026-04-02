# Pac-Man Multi-Agent Project

Ta projekt je del seminarske naloge s področja večagentnih sistemov.

## Osnova projekta
Za implementacijo uporabljamo odprtokodno Pac-Man rešitev kot osnovo:
- https://github.com/Abdelaal495/Multi-Agent-Pac-Man

## Zagon programa
Program lahko zaženemo z naslednjimi ukazi:

```bash
python pacman.py -p MinimaxAgent -l minimaxClassic -a depth=2
python pacman.py -p AlphaBetaAgent -l minimaxClassic -a depth=3
python pacman.py -p ExpectimaxAgent -l minimaxClassic -a depth=2
