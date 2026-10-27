# TIME QUEST

A compact, genuinely playable arcade survival game made with Python and Pygame. Move through a neon arena, collect glowing time orbs, and dodge the roaming hazards. Survive the full 100 seconds for the best run.

## Play on Windows

1. Install 64-bit Python 3.12 from [python.org](https://www.python.org/downloads/).
2. Open a terminal in this folder and install the dependency:
   ```
   py -3.12 -m pip install --upgrade pip
   py -3.12 -m pip install -r requirements.txt
   ```
3. Start the game:
   ```
   py -3.12 time_quest.py
   ```

## Controls

- **WASD** or **arrow keys** — move
- **Enter** or **Space** — start / restart
- **R** — restart after a run
- **Esc** — quit

## Game rules

Collect gold orbs for points. Each orb is worth more as the run progresses. Pink hazards cost one of your three lives; after a hit, you briefly flash and return to the center. Hazards arrive more often and move faster as time passes. The run ends when the 100-second timer expires or all lives are lost.

The game is self-contained: it draws its own graphics and needs no extra art or sound files. Pygame 2.6.1 is pinned because this version was used to verify the game.
