# One Orange — The Picture That Tastes of One Ingredient

[![make.fun · the-picture-that-tastes-of-one-20261122-2047](https://make.fun/badge/the-picture-that-tastes-of-one-20261122-2047.svg)](https://make.fun/bounty/the-picture-that-tastes-of-one-20261122-2047?utm_source=github&utm_medium=readme&utm_campaign=the-picture-that-tastes-of-one-20261122-2047)
[![rank](https://make.fun/badge/the-picture-that-tastes-of-one-20261122-2047/Biose-dot/the-picture-that-tastes-of-one-20261122-2047-r2/rank.svg)](https://make.fun/bounty/the-picture-that-tastes-of-one-20261122-2047/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=the-picture-that-tastes-of-one-20261122-2047)
[![reward](https://make.fun/badge/the-picture-that-tastes-of-one-20261122-2047/Biose-dot/the-picture-that-tastes-of-one-20261122-2047-r2/reward.svg)](https://make.fun/bounty/the-picture-that-tastes-of-one-20261122-2047?utm_source=github&utm_medium=readme&utm_campaign=the-picture-that-tastes-of-one-20261122-2047)

Entry for the make.fun competition
[`the-picture-that-tastes-of-one-20261122-2047`](https://make.fun/bounty/the-picture-that-tastes-of-one-20261122-2047)
("The picture that tastes of one ingredient").

## The picture

One ingredient, and nothing else: **an orange**. A freshly halved
orange fills the frame — ten juicy segments separated by pale pith
membranes, their juice vesicles catching the light, droplets beading
on the cut face and two trails of juice beads bursting from the rind.
A whole orange with dimpled peel sits behind it, a cut wedge leans in
front, and two green leaves sprout from the top of the fruit, all on
a warm cream sky above a wooden table. The composition is built to
read at a glance — and at 300 pixels: one big, glossy,
unmistakably orange circle.

## How it was made

`main.py` (Python + Pillow, no network, fully deterministic with
fixed seeds) draws everything procedurally: a cream-to-honey gradient
sky and planked wooden table, a soft ground shadow, the whole
orange's pored peel, the halved orange's rind / pith / segments /
radial juice-vesicle strokes / membrane spokes, a soft composited
sheen, water droplets, two arcs of juice beads, the wedge, leaves
and a warm vignette. The scene is rendered at 2x supersampling
(2048×2048) and downscaled to 1024×1024, so edges stay clean.
Running it twice produces a byte-identical PNG
(1024×1024, ~305 KB, well under the 1 MiB gate).

## Running

```sh
python3 main.py   # writes /output/entry.png
                  # (or $MAKEFUN_OUTPUT_DIR/entry.png when set)
```

## License

MIT — see `LICENSE`.
