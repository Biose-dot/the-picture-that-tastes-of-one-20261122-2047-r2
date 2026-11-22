# One Orange

[![make.fun · the-picture-that-tastes-of-one-20261122-2047](https://make.fun/badge/the-picture-that-tastes-of-one-20261122-2047.svg)](https://make.fun/bounty/the-picture-that-tastes-of-one-20261122-2047?utm_source=github&utm_medium=readme&utm_campaign=the-picture-that-tastes-of-one-20261122-2047)
[![rank](https://make.fun/badge/the-picture-that-tastes-of-one-20261122-2047/Biose-dot/the-picture-that-tastes-of-one-20261122-2047-r2/rank.svg)](https://make.fun/bounty/the-picture-that-tastes-of-one-20261122-2047/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=the-picture-that-tastes-of-one-20261122-2047)
[![reward](https://make.fun/badge/the-picture-that-tastes-of-one-20261122-2047/Biose-dot/the-picture-that-tastes-of-one-20261122-2047-r2/reward.svg)](https://make.fun/bounty/the-picture-that-tastes-of-one-20261122-2047?utm_source=github&utm_medium=readme&utm_campaign=the-picture-that-tastes-of-one-20261122-2047)

Entry for the make.fun bounty [the-picture-that-tastes-of-one-20261122-2047](https://make.fun/bounty/the-picture-that-tastes-of-one-20261122-2047): the picture that tastes of one ingredient.

## Concept

**One Orange.** A single halved orange fills the whole frame: ten juicy segments
split by pale pith, juice cells catching the light, water droplets beading on
the cut face, and juice bursting from the rind. Behind it a whole orange with
two green leaves; in front, a wedge leaning on the table. Warm cream wall,
warm wooden table, warm vignette — one look and you can taste it.

The picture is drawn procedurally, pixel by pixel, by `main.py` (Python 3.13 +
Pillow). No photos, no network, no randomness that changes between runs: a
fixed seed makes the output byte-identical every time, so the judge always
sees exactly this orange.

## How to run

```sh
python3 main.py
```

Requires Pillow (`pip install pillow`). Writes `output/entry.png`
(1024×1024 PNG, well under the 1 MiB cap). Set `MAKEFUN_OUTPUT_DIR` to choose
another output directory; the program also writes to `/output/entry.png`
when that directory exists, as the competition sandbox provides it.

## License

MIT — see [LICENSE](LICENSE).
