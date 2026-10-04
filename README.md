# Space Defense 2.0

A space-themed tower defense game for the browser. Deploy Laser, EMP, Cryo, and Railgun towers, upgrade your defenses, and survive multi-wave sectors and the Dreadnought boss.

**The primary version is now [`index.html`](index.html) at the repository root on `main`.** This is the HTML5 remake merged in [pull request #1](https://github.com/tomsikjr-cloud/SpaceDefense/pull/1). The original Python game is preserved in [`archive/python-v1/`](archive/python-v1/).

## Play locally

Download or clone this repository, then open `index.html` in a modern browser. No build step, Python installation, or package installation is required for the browser game.

Alternatively, if you have Python 3 installed, serve the repository folder:

```sh
python -m http.server 8000 --bind 127.0.0.1
```

Open <http://localhost:8000/> and select **Launch Campaign**. On phones and tablets, landscape orientation is recommended.

The game uses Canvas 2D and Web Audio, with graphics and sound generated in the page. Google Fonts supplies optional typefaces; system fonts are used when they are unavailable. High scores are stored locally in your browser, so they can differ between browsers and file/localhost addresses. Audio begins after user interaction.

## Controls

- Click or tap a tower in the dock, then a free grid cell to place it. Shift-click places several.
- Click a placed tower to upgrade, sell, or choose First, Strong, or Near targeting.
- Use **Launch Wave** to begin a wave; launching the next wave early earns bonus credits.
- Use the top controls for speed, pause, and sound.

| Shortcut | Action |
| --- | --- |
| 1 / 2 / 3 / 4 | Select Laser / EMP / Cryo / Railgun |
| U / S | Upgrade / sell the selected tower |
| N / Enter | Launch a wave during play |
| Space / P | Toggle pause |
| F | Cycle game speed |
| M | Toggle sound |
| Esc / right-click | Cancel selection (Esc also resumes when paused) |

## Repository layout

```text
index.html                 Primary browser game (v2)
v2/index.html              Compatibility redirect to the root game
archive/python-v1/         Original Python game and its level data
```

The browser game's code, styles, and game data live in `index.html`. Tower balance, enemy stats, and sectors are configured in `TOWERS`, `ENEMIES`, and `LEVELS` inside that file. It does not load the archived `levels.json`.

## Legacy version and history

See the [archive README](archive/python-v1/README.md) for the Python/Pygame version and how to run it. Its source and level data are preserved unchanged. Git history retains the original files, the v2 contribution by [darthmodrost](https://github.com/darthmodrost), and the merge commit `87d946979c8538dd4b21abb1a5c72344f8b95e0f`.
