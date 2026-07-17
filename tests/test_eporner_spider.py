"""Unit tests for eporner_spider.py — HTML parsing, URL building, dedup."""
import json
import sys
import unittest
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import eporner_spider


SAMPLE_BLOCK = """
<div class="mb" data-id="12877969" data-vp="12877969|0|2" id="vf12877969">
<div class="mbimg"><div class="mbcontent">
<a href="/video-sEPxStHywtE/cupi-cupita-gunungnya-gede-banget/">
<img src="https://static-sg-cdn.eporner.com/thumbs/static4/1/12/128/12877969/9_240.jpg" alt="Cupi Cupita Gunungnya Gede Banget" />
</a>
<div class="mvhdico" title="Quality"><span>480p</span></div>
</div></div>
<div class="mbunder">
<p class="mbtit"><a href="/video-sEPxStHywtE/cupi-cupita-gunungnya-gede-banget/">Cupi Cupita Gunungnya Gede Banget</a></p>
<p class="mbstats">
<span class="mbtim" title="Duration">8:51</span>
<span class="mbrate" title="Rating">73%</span>
<span class="mbvie" title="Views">1,826,445</span>
<span class="mb-uploader"><a href="/profile/Olenamikaze27/" title="Uploader">Olenamikaze27</a></span>
</p>
</div>
</div>
"""


class TestParseVideoBlocks(unittest.TestCase):
    def test_parse_single_block(self):
        videos = eporner_spider._parse_video_blocks(SAMPLE_BLOCK)
        self.assertEqual(len(videos), 1)
        v = videos[0]
        self.assertEqual(v["eid"], "sEPxStHywtE")
        self.assertEqual(v["video_id"], 12877969)
        self.assertEqual(v["title"], "Cupi Cupita Gunungnya Gede Banget")
        self.assertEqual(v["duration"], "8:51")
        self.assertEqual(v["quality"], "480p")
        self.assertEqual(v["uploader"], "Olenamikaze27")
        self.assertEqual(v["views"], "1,826,445")
        self.assertIn("12877969/9_240.jpg", v["thumbnail"])
        self.assertEqual(v["page_url"], "/video-sEPxStHywtE/cupi-cupita-gunungnya-gede-banget/")

    def test_parse_multiple_blocks(self):
        html = SAMPLE_BLOCK + SAMPLE_BLOCK.replace("12877969", "10430138").replace("sEPxStHywtE", "uRVcnjF4bwg")
        videos = eporner_spider._parse_video_blocks(html)
        self.assertEqual(len(videos), 2)
        self.assertEqual(videos[0]["eid"], "sEPxStHywtE")
        self.assertEqual(videos[1]["eid"], "uRVcnjF4bwg")

    def test_parse_empty(self):
        videos = eporner_spider._parse_video_blocks("<html></html>")
        self.assertEqual(videos, [])

    def test_parse_missing_optional_fields(self):
        html = """
        <div class="mb" data-id="99999">
        <div class="mbimg"><div class="mbcontent">
        <a href="/video-abc123/some-title/">
        <img src="https://cdn.test/thumb.jpg" alt="Some Title" />
        </a>
        </div></div>
        <div class="mbunder">
        <p class="mbtit"><a href="/video-abc123/some-title/">Some Title</a></p>
        <p class="mbstats">
        <span class="mbtim" title="Duration">5:00</span>
        </p>
        </div>
        </div>
        """
        videos = eporner_spider._parse_video_blocks(html)
        self.assertEqual(len(videos), 1)
        v = videos[0]
        self.assertEqual(v["eid"], "abc123")
        self.assertEqual(v["video_id"], 99999)
        self.assertEqual(v["title"], "Some Title")
        self.assertEqual(v["duration"], "5:00")
        self.assertEqual(v.get("quality"), "")
        self.assertEqual(v.get("uploader"), "")
        self.assertEqual(v.get("views"), "")

    def test_hd_quality(self):
        html = SAMPLE_BLOCK.replace("480p", "1080p")
        videos = eporner_spider._parse_video_blocks(html)
        self.assertEqual(videos[0]["quality"], "1080p")

    def test_views_with_thousands_separator(self):
        videos = eporner_spider._parse_video_blocks(SAMPLE_BLOCK)
        self.assertEqual(videos[0]["views"], "1,826,445")


class TestBuildUrl(unittest.TestCase):
    def test_page_1(self):
        url = eporner_spider._build_url("amateur", 1)
        self.assertEqual(url, "https://www.eporner.com/cat/amateur/")

    def test_page_2(self):
        url = eporner_spider._build_url("amateur", 2)
        self.assertEqual(url, "https://www.eporner.com/cat/amateur/page-2/")

    def test_custom_category(self):
        url = eporner_spider._build_url("lingerie", 3)
        self.assertEqual(url, "https://www.eporner.com/cat/lingerie/page-3/")


class TestLoadExistingEids(unittest.TestCase):
    def setUp(self):
        self.original_file = eporner_spider.XV_VIDEOS_FILE
        self.tmpdir = tempfile.TemporaryDirectory()
        eporner_spider.XV_DIR = Path(self.tmpdir.name)
        eporner_spider.XV_VIDEOS_FILE = eporner_spider.XV_DIR / "videos.jsonl"

    def tearDown(self):
        eporner_spider.XV_VIDEOS_FILE = self.original_file
        self.tmpdir.cleanup()

    def test_no_file(self):
        self.assertEqual(eporner_spider.load_existing_eids(), set())

    def test_loads_eids(self):
        eporner_spider.XV_DIR.mkdir(parents=True, exist_ok=True)
        eporner_spider.XV_VIDEOS_FILE.write_text(
            '{"eid":"abc123","source":"eporner"}\n{"eid":"def456","source":"eporner"}\n'
        )
        eids = eporner_spider.load_existing_eids()
        self.assertEqual(eids, {"abc123", "def456"})


class TestAppendVideos(unittest.TestCase):
    def setUp(self):
        self.original_file = eporner_spider.XV_VIDEOS_FILE
        self.tmpdir = tempfile.TemporaryDirectory()
        eporner_spider.XV_DIR = Path(self.tmpdir.name)
        eporner_spider.XV_VIDEOS_FILE = eporner_spider.XV_DIR / "videos.jsonl"

    def tearDown(self):
        eporner_spider.XV_VIDEOS_FILE = self.original_file
        self.tmpdir.cleanup()

    def test_append_creates_file(self):
        eporner_spider._append_videos([{"eid": "test1", "source": "eporner"}])
        self.assertTrue(eporner_spider.XV_VIDEOS_FILE.exists())
        lines = eporner_spider.XV_VIDEOS_FILE.read_text().strip().split("\n")
        self.assertEqual(len(lines), 1)

    def test_append_preserves_existing(self):
        eporner_spider.XV_DIR.mkdir(parents=True, exist_ok=True)
        eporner_spider.XV_VIDEOS_FILE.write_text('{"eid":"old","source":"xvideos"}\n')
        eporner_spider._append_videos([{"eid": "new", "source": "eporner"}])
        lines = eporner_spider.XV_VIDEOS_FILE.read_text().strip().split("\n")
        self.assertEqual(len(lines), 2)


if __name__ == "__main__":
    unittest.main()
