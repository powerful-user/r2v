---
name: r2v
description: Use when turning a raster image (PNG, JPG, TIFF, BMP, GIF, PSD) such as a logo, icon, line art, scan, stamp, signature or pixel art into an SVG, or when asked to vectorize or trace an image. Traces black-and-white art into filled paths, smoothly with potrace or pixel-exact.
---

# r2v

`r2v` traces the black regions of an image into filled SVG paths that keep
the source's pixel size. Transparency is flattened onto white and the image
is thresholded to 1-bit first, so the result is always one color: color,
grays and shading become solid black or nothing.

The script is `scripts/r2v` next to this file. Set
`R2V=<this skill's directory>/scripts/r2v` and run it with `python3 "$R2V"`
(installs can drop the executable bit).

## Steps

1. **Check the tools.** Run `magick -version` and `potrace --version`.
   r2v needs ImageMagick 7 (the `magick` command, not just `convert`),
   potrace and Python 3; `--exact` does not use potrace. If one is missing,
   tell the user and offer the install (`brew install imagemagick potrace`
   on macOS, `sudo apt install imagemagick potrace` on Debian/Ubuntu, where
   older releases ship ImageMagick 6 and need a newer build). Ask before
   installing anything.

2. **Look at the image** (view it if you can, and run
   `magick identify FILE`), then pick the mode:

   | What you see | Do |
   |---|---|
   | Dark art on a light or transparent background | default (smooth curves) |
   | Light art on a dark background | `--invert` |
   | Pixel art, dithering, or the user wants hard pixel edges kept | `--exact` |
   | A color photo or soft shading | say in one sentence that the SVG will be a one-color silhouette of everything darker than the threshold you name (50% unless you pass `--threshold`), then trace if the user wants speed, or ask |

   To check the background, `magick FILE -background white -alpha remove
   -colorspace gray -format '%[fx:mean]' info:` prints the mean brightness:
   well below 0.5 means mostly dark, so the art is probably light.

3. **Trace.**

   ```bash
   python3 "$R2V" in.png -o out.svg --check            # smooth
   python3 "$R2V" in.png -o out.svg --exact --check    # pixel-exact
   python3 "$R2V" images/ -o svgs/ --check             # every image in a folder
   ```

   | Flag | Default | Effect |
   |---|---|---|
   | `--threshold N` | 50 | Pixels darker than N% count as black. Raise it to keep faint lines, lower it to drop a gray background. |
   | `--turdsize N` | 2 (0 with `--exact`) | Drop specks and holes up to N pixels. |
   | `--smooth N` | 1.0 | 0 gives sharp polygons, 1.334 all curves. Ignored with `--exact`. |
   | `--invert` | off | Trace light art on a dark background. |
   | `--exact` | off | Follow pixel edges instead of fitting curves. |
   | `--check` | off | Render each SVG back and report differing pixels. |

   A layered PSD or multi-page file traces only its first image.

4. **Check the result.** Trace with `--check` added: r2v renders each SVG
   back (headless Chrome, or ImageMagick when Chrome is missing) and
   prints how many pixels differ from the 1-bit source. `--exact` should
   give 0 with Chrome; ImageMagick may be off by a few pixels. Smooth output differs only along edges, usually
   under 2%. The check proves the SVG matches the thresholded image, not
   that you traced the right thing: view the SVG if you can, and if the
   art came out as a hole in a filled rectangle, retrace with `--invert`.
   For specks or broken lines, adjust `--turdsize` or `--threshold`.

5. **Report** the output path, the mode and flags, the threshold as a
   number (50% unless set, not "default"), what the
   check showed, and that the paths are filled black: to recolor, change
   `fill="#000000"` in the SVG.

## Never

- Wrap the raster in an SVG `<image>` and call it a vector.
- Hand-roll a `magick | potrace` pipeline instead of r2v. It loses the
  transparency flattening and sizes the SVG in points, not pixels.
- Trace a color or grayscale image without telling the user it becomes
  one color.
- Report success without `--check`, or hide a nonzero `--exact` count.
- Install packages without asking.
