import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

R2V = Path(__file__).resolve().parent.parent / "r2v"


def magick(*args):
    subprocess.run(["magick", *args], check=True)


def run_r2v(*args):
    return subprocess.run(
        [sys.executable, str(R2V), *map(str, args)],
        capture_output=True,
        text=True,
    )


def path_count(svg):
    return len(re.findall(r"<path\b", svg))


class SingleFileTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def test_traces_black_shape_into_svg_with_image_dimensions(self):
        src = self.tmp / "circle.png"
        magick("-size", "200x100", "xc:white", "-fill", "black",
               "-draw", "circle 100,50 100,10", str(src))
        out = self.tmp / "circle.svg"

        result = run_r2v(src, "-o", out)

        self.assertEqual(result.returncode, 0, result.stderr)
        svg = out.read_text()
        self.assertIn('width="200px" height="100px" viewBox="0 0 200 100"', svg)
        self.assertGreater(path_count(svg), 0)

    def test_transparent_background_traces_like_white(self):
        traced = {}
        for bg in ("white", "none"):
            src = self.tmp / f"{bg}.png"
            magick("-size", "200x100", f"xc:{bg}", "-fill", "black",
                   "-draw", "circle 100,50 100,10", str(src))
            out = self.tmp / f"{bg}.svg"
            result = run_r2v(src, "-o", out)
            self.assertEqual(result.returncode, 0, result.stderr)
            traced[bg] = out.read_text()

        self.assertEqual(traced["none"], traced["white"])

    def test_multi_image_file_traces_only_first_image(self):
        # Layered PSDs and multi-page TIFFs read as several images; the
        # first is the flattened composite / first page.
        circle = self.tmp / "circle.png"
        magick("-size", "200x100", "xc:white", "-fill", "black",
               "-draw", "circle 100,50 100,10", str(circle))
        layered = self.tmp / "layered.tif"
        magick(str(circle), "-size", "200x100", "xc:black", str(layered))

        run_r2v(circle, "-o", self.tmp / "circle.svg")
        result = run_r2v(layered, "-o", self.tmp / "layered.svg")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.tmp / "layered.svg").read_text(),
                         (self.tmp / "circle.svg").read_text())


    def test_unreadable_input_fails_with_message_not_traceback(self):
        result = run_r2v(self.tmp / "missing.png", "-o", self.tmp / "out.svg")

        self.assertEqual(result.returncode, 1)
        self.assertIn("missing.png", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


class OptionsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def trace(self, name, *draw, bg="white", args=()):
        src = self.tmp / f"{name}.png"
        magick("-size", "200x100", f"xc:{bg}", *draw, str(src))
        out = self.tmp / f"{name}.svg"
        result = run_r2v(src, "-o", out, *args)
        self.assertEqual(result.returncode, 0, result.stderr)
        return out.read_text()

    CIRCLE = ("-fill", "black", "-draw", "circle 100,50 100,10")

    def test_invert_traces_white_art_on_black(self):
        normal = self.trace("normal", *self.CIRCLE)
        inverted = self.trace("inverted", "-fill", "white",
                              "-draw", "circle 100,50 100,10",
                              bg="black", args=["--invert"])
        self.assertEqual(inverted, normal)

    def test_threshold_decides_which_grays_count_as_black(self):
        gray = ("-fill", "gray50", "-draw", "circle 100,50 100,10")
        self.assertGreater(path_count(self.trace("dark", *gray, args=["--threshold", "60"])), 0)
        self.assertEqual(path_count(self.trace("light", *gray, args=["--threshold", "40"])), 0)

    def test_turdsize_drops_small_specks(self):
        clean = self.trace("clean", *self.CIRCLE)
        speck = (*self.CIRCLE, "-draw", "rectangle 5,5 7,7")  # 9 px
        self.assertNotEqual(self.trace("kept", *speck), clean)
        self.assertEqual(self.trace("dropped", *speck, args=["--turdsize", "10"]), clean)

    def test_smooth_zero_gives_straight_segments_only(self):
        svg = self.trace("poly", *self.CIRCLE, args=["--smooth", "0"])
        self.assertGreater(path_count(svg), 0)
        self.assertNotRegex(svg, r'd="[^"]*c')


CHROME = shutil.which("google-chrome") or shutil.which("chromium")


@unittest.skipUnless(CHROME, "needs Chrome to render SVG faithfully")
class ExactTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def differing_pixels(self, src, svg, size):
        # ImageMagick's built-in SVG renderer bleeds edges and ignores
        # holes, so render with Chrome.
        ref, shot, back = (self.tmp / n for n in ("ref.pbm", "shot.png", "back.pbm"))
        magick(str(src), "-background", "white", "-alpha", "remove",
               "-colorspace", "gray", "-threshold", "50%", str(ref))
        subprocess.run([CHROME, "--headless", "--disable-gpu", "--hide-scrollbars",
                        "--force-device-scale-factor=1",
                        f"--window-size={size.replace('x', ',')}",
                        f"--screenshot={shot}", svg.as_uri()],
                       check=True, capture_output=True)
        magick(str(shot), "-background", "white", "-alpha", "remove",
               "-colorspace", "gray", "-threshold", "50%", str(back))
        result = subprocess.run(["magick", "compare", "-metric", "AE",
                                 str(ref), str(back), "null:"],
                                capture_output=True, text=True)
        return int(float(result.stderr.split()[0]))

    def test_exact_reproduces_every_pixel_of_dithered_art(self):
        # Ordered dither gives single pixels, diagonal touches and holes.
        src = self.tmp / "dither.png"
        magick("-size", "64x48", "gradient:black-white", "-rotate", "90",
               "-resize", "64x48!", "-ordered-dither", "o4x4",
               "-fill", "black", "-draw", "rectangle 4,4 20,20",
               "-fill", "white", "-draw", "rectangle 9,9 14,14", str(src))
        out = self.tmp / "dither.svg"

        result = run_r2v(src, "-o", out, "--exact")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('width="64px" height="48px" viewBox="0 0 64 48"', out.read_text())
        self.assertEqual(self.differing_pixels(src, out, "64x48"), 0)

    def test_exact_keeps_single_pixels_unless_turdsize_given(self):
        src = self.tmp / "specks.png"
        magick("-size", "8x6", "xc:white", "-fill", "black",
               "-draw", "rectangle 1,1 4,3", "-draw", "point 6,4",
               "-fill", "white", "-draw", "point 2,2", str(src))
        kept, dropped = self.tmp / "kept.svg", self.tmp / "dropped.svg"

        run_r2v(src, "-o", kept, "--exact")
        run_r2v(src, "-o", dropped, "--exact", "--turdsize", "1")

        # Block, its one-pixel hole, and the one-pixel speck.
        self.assertEqual(kept.read_text().count("M"), 3)
        self.assertEqual(dropped.read_text().count("M"), 1)


class FolderTest(unittest.TestCase):
    def test_traces_every_image_in_folder_and_skips_other_files(self):
        tmp = Path(tempfile.mkdtemp())
        src = tmp / "images"
        src.mkdir()
        for name in ("a.png", "b.JPG"):
            magick("-size", "50x50", "xc:white", "-fill", "black",
                   "-draw", "rectangle 10,10 40,40", str(src / name))
        (src / "notes.txt").write_text("not an image")
        out = tmp / "svgs"

        result = run_r2v(src, "-o", out)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(sorted(p.name for p in out.iterdir()), ["a.svg", "b.svg"])


if __name__ == "__main__":
    unittest.main()
