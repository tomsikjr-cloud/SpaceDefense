# Space Defense: original Python version

This directory archives the original Pygame game. The primary, browser-based version is now [`../../index.html`](../../index.html).

`Space_Defense.py` and `levels.json` were moved here together without changing their contents. They remain available for reference or local play; the browser version does not depend on them.

## Run the archived game

With Python 3 and Pygame available, run these commands from the repository root:

```sh
python -m pip install pygame
cd archive/python-v1
python Space_Defense.py
```

Run from this directory because the original code reads `levels.json` and writes `highscore.json` relative to the current working directory. Generated high scores and Python caches are ignored by Git.

The original root paths are also preserved in Git history before the archive move. The archive has not been updated or retested for current Python/Pygame releases.
