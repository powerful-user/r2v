# r2v skill pressure scenarios

Each scenario runs in a fresh, empty working directory holding only its
fixture. The baseline run has no skill; the result run has the `r2v` skill
installed with `npx skills add <this repo> --skill r2v`. A runner reads a
scenario only up to its Expected with skill line:

```
awk -v id='### SNN:' 'index($0,id)==1 {p=1} p && /^Expected with skill/ {exit} p' tests/scenarios.md
```

### S1: transparent logo to scalable SVG

Setup: ImageMagick 7, potrace, Python 3 and headless Chrome are installed.

Fixture: `logo.png`, 400x200, transparent background, a black filled circle
and a black bar.

```
magick -size 400x200 xc:none -fill black -draw "circle 100,100 100,30" \
  -draw "rectangle 200,80 370,120" logo.png
```

Prompt: "Convert logo.png into an SVG I can scale up for print. Save it as logo.svg."

Expected with skill: traces with the skill's bundled `r2v` in smooth mode (no
`--exact`, no `--invert`). `logo.svg` holds filled vector paths, keeps
`width="400px" height="200px" viewBox="0 0 400 200"`, and contains no
`<image>` or base64 raster. The agent checks the output before reporting.

Baseline: 2026-11-10, Sonnet subagent, no skill. Did not find r2v; flattened alpha by hand and piped `magick` into `potrace -s`. Paths are fine and it checked with `magick compare` (0.87% differ), but the SVG is sized `400pt x 200pt`, not pixels.

Result: PASS, 2026-11-10, Sonnet subagent. Read the skill, checked tools and mean brightness (0.718), viewed the PNG, ran `r2v logo.png -o logo.svg --check` (111 of 80000 differ, Chrome). Output is `400px x 200px`, two paths, no `<image>`; told the user how to recolor. Chrome render coverage 0.281 matches the source.

Rerun after the threshold change: PASS, 2026-11-10, Sonnet subagent. Same smooth trace (111 of 80000 differ, Chrome render coverage 0.281); its report named the 50% threshold.

### S2: pixel art that must stay pixel-exact

Setup: as S1.

Fixture: `sprite.png`, 32x32 1-bit pixel art with single-pixel steps and a
checkerboard dither.

```
magick -size 32x32 xc:white -fill black -draw "rectangle 4,4 27,27" \
  -fill white -draw "rectangle 8,8 23,23" \
  \( -size 8x8 pattern:gray50 \) -geometry +12+12 -composite \
  -fill black -draw "point 2,2" -alpha off -threshold 50% -type bilevel sprite.png
```

Prompt: "Vectorize sprite.png to sprite.svg. It's pixel art, so every pixel has to stay exactly where it is, no smoothing or rounded corners."

Expected with skill: uses `r2v --exact`, so the path is axis-aligned
`h`/`v` steps and the lone pixel and every dither dot survive (turdsize 0).
The agent confirms the result matches the source pixels, for example by
rendering it back and comparing, or says plainly that it did not.

Baseline: 2026-11-10, Sonnet subagent, no skill, on the corrected fixture (a first fixture left the black pixels transparent and was discarded). Wrote an inline Python run-length emitter of 1-pixel-tall rects; geometry was right, confirmed by parsing the path back. ImageMagick's render differed by 130 pixels and it blamed the renderer without being able to confirm it. No pixel-exact tool, and no faithful check.

Result: PASS, 2026-11-10, Sonnet subagent. Ran `r2v sprite.png -o sprite.svg --exact --check`: 0 of 1024 pixels differ in Chrome. Path is `h`/`v` steps with the lone pixel at (2,2) and every dither dot; `32px x 32px`.

Rerun after the threshold change: PASS, 2026-11-10, Sonnet subagent. `--exact --check`, 0 of 1024 differ; named the 50% threshold.

### S3: white artwork on a black background

Setup: as S1.

Fixture: `negative.png`, 300x300, black background with a white star.

```
magick -size 300x300 xc:black -fill white \
  -draw "polygon 150,20 185,115 285,115 205,175 235,275 150,215 65,275 95,175 15,115 115,115" \
  negative.png
```

Prompt: "Turn the white star in negative.png into an SVG (star.svg)."

Expected with skill: sees the art is white on black and uses `--invert`, so
the SVG's path is the star, not a 300x300 rectangle with a star-shaped hole.
It tells the user the paths are filled black and how to recolor them.

Baseline: 2026-11-10, Sonnet subagent, no skill. Viewed the image, negated it and piped into `potrace -s`; checked ink coverage against the source (within 1%) and told the user the fill is black. Correct shape, but sized in `pt`, and it wrote a stray file to `/tmp` before cleaning it up.

Result: PASS, 2026-11-10, Sonnet subagent. Mean brightness 0.267 led it to `--invert`; `--check` gave 63 of 90000 differ. Chrome render coverage 0.266 matches the star's 0.267, so it traced the star, not the background. Told the user the fill is black and how to recolor.

Rerun after the threshold change: PASS, 2026-11-10, Sonnet subagent. Mean brightness 0.267 led to `--invert`; 63 of 90000 differ; Chrome render coverage 0.266 matches the star; named the 50% threshold.

### S4: color photo under time pressure

Setup: as S1.

Fixture: `photo.jpg`, 320x240, a color gradient with a soft-edged red
ellipse.

```
magick -size 320x240 gradient:skyblue-orange -fill red \
  -draw "ellipse 160,120 80,50 0,360" -blur 0x6 photo.jpg
```

Prompt: "Make photo.jpg into an SVG, quick, I don't need a lecture."

Expected with skill: says in a sentence that r2v makes a one-color (black)
trace, so color and shading are lost, then either traces with a stated
threshold or asks which the user wants. It never wraps the JPEG in an SVG
`<image>` and calls it vector.

Baseline: 2026-11-10, Sonnet subagent, no skill. Thresholded and traced with `potrace -s` straight away and sent the user no message at all, so the loss of color went unmentioned. SVG sized in `pt`. (Its report shows it knew of the r2v repository from session context, a leak in the baseline harness.)

Result: PASS, 2026-11-10, Sonnet subagent. Traced with `r2v --check` (89 of 76800 differ) and its reply said the SVG is a one-color black silhouette and how to recolor. It called the trace "default" rather than naming the 50% threshold. No `<image>`; `320px x 240px`.

Rerun after the threshold change: PASS, 2026-11-10, Sonnet subagent. Its reply named the threshold ("a one-color silhouette of everything darker than 50%") and how to recolor; 89 of 76800 differ, and Chrome render coverage 0.169 matches the source's 0.170 below 50%. It skipped step 2's look at the image and judged it a color photo from `magick identify` (sRGB) and the filename.
