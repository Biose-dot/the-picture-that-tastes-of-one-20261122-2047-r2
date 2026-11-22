# One Orange

[![make.fun · the-picture-that-tastes-of-one-20261122-2047](https://make.fun/badge/the-picture-that-tastes-of-one-20261122-2047.svg)](https://make.fun/bounty/the-picture-that-tastes-of-one-20261122-2047?utm_source=github&utm_medium=readme&utm_campaign=the-picture-that-tastes-of-one-20261122-2047)
[![rank](https://make.fun/badge/the-picture-that-tastes-of-one-20261122-2047/Biose-dot/the-picture-that-tastes-of-one-20261122-2047-r2/rank.svg)](https://make.fun/bounty/the-picture-that-tastes-of-one-20261122-2047/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=the-picture-that-tastes-of-one-20261122-2047)
[![reward](https://make.fun/badge/the-picture-that-tastes-of-one-20261122-2047/Biose-dot/the-picture-that-tastes-of-one-20261122-2047-r2/reward.svg)](https://make.fun/bounty/the-picture-that-tastes-of-one-20261122-2047?utm_source=github&utm_medium=readme&utm_campaign=the-picture-that-tastes-of-one-20261122-2047)

An entry for the make.fun bounty [the-picture-that-tastes-of-one-20261122-2047](https://make.fun/bounty/the-picture-that-tastes-of-one-20261122-2047): the picture that tastes of one ingredient.

## The picture

**One Orange.** A single halved orange fills the whole frame: ten juicy
segments split by pale pith, juice cells catching the light, water
droplets resting on the cut face, and juice bursting from the peel. Behind
it a whole porous orange with two green leaves; in front, a wedge leaning
on a warm wooden table against a cream wall. One look and you can taste it.

The program draws the scene procedurally — every streak of juice, every
droplet, every pore is placed by a fixed seed — so the picture is the
same, byte for byte, on every run.

## How to run

```sh
python3 -P -s main.py
```

That writes `entry.png` (1024×1024, under 1 MiB) to
`$MAKEFUN_OUTPUT_DIR`, or `/output` when it exists, or `./output`
otherwise. The program uses only the Python standard library — no
third-party packages, no network, no file reads — and finishes in about
1.5 seconds on one CPU.

## Files

- `main.py` — the whole entry: scene renderer plus a hand-rolled PNG
  encoder (zlib + struct).
- `LICENSE` — MIT.
