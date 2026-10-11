# Space Defense 2.0

A space-themed tower defense game for the browser. Deploy Laser, EMP, Cryo, and Railgun towers, upgrade your defenses, and survive multi-wave sectors and the Dreadnought boss.

## Play

Download or clone this repository, then open `index.html` in a modern browser and select **Launch Campaign**. No installation or build step is required. On phones and tablets, landscape orientation is recommended.

You can also serve the repository with any static web server; `index.html` is the entry point.

## Features

- Four tower types with upgrades and selectable targeting.
- Multi-wave sectors, early-launch bonuses, and a Dreadnought boss.
- Mouse and touch controls, plus optional keyboard shortcuts.
- Adjustable game speed, pause, and synthesized sound.
- Local high scores saved in your browser.

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

## Development

The game is a single HTML file using Canvas 2D and Web Audio. Code, styles, and game data live in [`index.html`](index.html). Tower balance, enemy stats, and sectors are configured in `TOWERS`, `ENEMIES`, and `LEVELS` inside that file.

`v2/index.html` redirects older links to the root game.

Graphics and sound are generated in the page. Google Fonts supplies optional typefaces; system fonts are used when they are unavailable. Audio begins after user interaction. High scores are stored locally and can differ between browsers and file/server addresses.

## Credits

Browser game contributed by [darthmodrost](https://github.com/darthmodrost) in [pull request #1](https://github.com/tomsikjr-cloud/SpaceDefense/pull/1).
