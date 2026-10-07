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

Layered PSDs and multi-page files trace only the first image (the flattened
composite for a PSD).

## Tests

```bash
python3 -m unittest discover -s tests
```

The `--exact` round-trip tests render with headless Chrome (ImageMagick's
built-in SVG renderer is not faithful) and skip when Chrome is missing.
