# raster-to-vector

`r2v` traces black-and-white raster images (PNG, JPG, TIFF, BMP, GIF, PSD)
into SVG. ImageMagick flattens transparency onto white and thresholds the
image to 1-bit; potrace turns the black regions into smooth filled paths,
or, with `--exact`, `r2v` outlines them along the pixel grid so every hard
edge and dither dot survives unchanged. The SVG keeps the source's pixel
dimensions.

## Requirements

- ImageMagick 7 (`magick`)
- potrace (`sudo apt install potrace`)
- Python 3

## Usage

```bash
./r2v logo.png -o logo.svg          # one file
./r2v images/ -o svgs/              # every image in a folder -> svgs/<name>.svg
./r2v grunge.jpg -o grunge.svg --exact   # pixel-exact edges, no smoothing
```

| Flag | Default | Effect |
|---|---|---|
| `--threshold N` | 50 | Pixels darker than N% brightness count as black. |
| `--turdsize N` | 2 (0 with `--exact`) | Drop specks and holes of up to N pixels. |
| `--smooth N` | 1.0 | Corner rounding: 0 gives sharp polygons, 1.334 all curves. Ignored with `--exact`. |
| `--invert` | off | Trace white art on a black background. |
| `--exact` | off | Follow pixel edges exactly instead of fitting curves. |
| `--check` | off | Render each SVG back (headless Chrome, else ImageMagick) and print how many pixels differ from the 1-bit source. |

Layered PSDs and multi-page files trace only the first image (the flattened
composite for a PSD).

## Agent skill

The repository ships an [Agent Skill](https://skills.sh) in `skills/r2v/`
that teaches coding agents (Claude Code, Codex, Cursor and others) when to
reach for `r2v`, which mode to pick, and how to check the result. The
script itself lives in `skills/r2v/scripts/r2v`, so the skill carries it;
`./r2v` at the root is a symlink to it. Install it with:

```bash
npx skills add powerful-user/r2v
```

The agent still needs ImageMagick 7, potrace and Python 3 on the machine.

## Tests

```bash
python3 -m unittest discover -s tests
```

The `--exact` round-trip and `--check` tests render with headless Chrome
(ImageMagick's built-in SVG renderer is not faithful) and skip when Chrome
is missing. `tests/scenarios.md` holds the pressure scenarios for the agent
skill.
