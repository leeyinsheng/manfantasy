"""Unit tests for xv_spider.py — URL building, HTML parsing, dedup."""
import json
import sys
import unittest
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import xv_spider


class TestUrlBuilding(unittest.TestCase):
    def test_category_url_page0(self):
        src = {"type": "category", "id": "Lingerie-83", "sort": "uploaddate"}
        url = xv_spider._build_url(src, 0)
        self.assertEqual(url, "https://www.xvideos.com/c/Lingerie-83?s=uploaddate")

    def test_category_url_page2(self):
        src = {"type": "category", "id": "Lingerie-83", "sort": "uploaddate"}
        url = xv_spider._build_url(src, 2)
        self.assertEqual(url, "https://www.xvideos.com/c/Lingerie-83/2?s=uploaddate")

    def test_search_url_page0(self):
        src = {"type": "search", "id": "日本", "keyword": "日本", "sort": "uploaddate"}
        url = xv_spider._build_url(src, 0)
        self.assertIn("?k=%E6%97%A5%E6%9C%AC", url)
        self.assertIn("sort=uploaddate", url)

    def test_search_url_page3(self):
        src = {"type": "search", "id": "日本", "keyword": "日本", "sort": "uploaddate"}
        url = xv_spider._build_url(src, 3)
        self.assertIn("p=3", url)
        self.assertIn("k=%E6%97%A5%E6%9C%AC", url)

    def test_search_keyword_encoding(self):
        src = {"type": "search", "id": "中國", "keyword": "中國", "sort": "uploaddate"}
        url = xv_spider._build_url(src, 0)
        self.assertIn("k=%E4%B8%AD%E5%9C%8B", url)


class TestHtmlParsing(unittest.TestCase):
    def test_parse_single_block(self):
        html = """
        <div id="video_khluvuo33b8" data-id="51923269" data-eid="khluvuo33b8"
             class="frame-block thumb-block">
        <div class="thumb-inside"><div class="thumb"><a href="/video.khluvuo33b8/test">
        <img data-src="https://thumb-cdn.xvideos.com/test.jpg" data-idcdn="21"/>
        <span class="video-hd-mark">1080p</span></a></div></div>
        <div class="thumb-under"><p class="title"><a href="/video.khluvuo33b8/test"
        title="Test Video Title">Test Video Title <span class="duration">48 min</span></a></p>
        <p class="metadata"><span class="bg"><span class="duration">48 min</span>
        <span><a href="/testuser"><span class="name">TestUser</span></a>
        <span> - </span><span>68.1k Views</span></span></span></p></div>
        </div>
        """
        videos = xv_spider._parse_video_blocks(html)
        self.assertEqual(len(videos), 1)
        v = videos[0]
        self.assertEqual(v["eid"], "khluvuo33b8")
        self.assertEqual(v["video_id"], 51923269)
        self.assertEqual(v["title"], "Test Video Title")
        self.assertEqual(v["duration"], "48 min")
        self.assertEqual(v["quality"], "1080p")
        self.assertEqual(v["uploader"], "TestUser")
        self.assertEqual(v["views"], "68.1k views")
        self.assertIn("test.jpg", v["thumbnail"])

    def test_parse_sd_quality(self):
        html = """
        <div id="video_khluvuo33b8" data-id="51923269" data-eid="khluvuo33b8"
             class="frame-block thumb-block">
        <div class="thumb"><a href="/video.khluvuo33b8/test">
        <span class="video-sd-mark">360p</span></a></div>
        <div class="thumb-under"><p class="title"><a href="#" title="SD Video">
        SD Video <span class="duration">5 min</span></a></p>
        <p class="metadata"><span class="bg"><span class="duration">5 min</span>
        <a href="/test"><span class="name">Tester</span></a></span></p></div>
        </div>
        """
        videos = xv_spider._parse_video_blocks(html)
        self.assertEqual(len(videos), 1)
        self.assertEqual(videos[0]["quality"], "360p")

    def test_parse_no_quality(self):
        html = """
        <div id="video_khluvuo33b8" data-id="51923269" data-eid="khluvuo33b8"
             class="frame-block thumb-block">
        <div class="thumb-under"><p class="title"><a href="#" title="No Quality">
        No Quality <span class="duration">10 min</span></a></p>
        <p class="metadata"><span class="bg"><span class="duration">10 min</span>
        <a href="/test"><span class="name">Tester</span></a></span></p></div>
        </div>
        """
        videos = xv_spider._parse_video_blocks(html)
        self.assertEqual(len(videos), 1)
        self.assertEqual(videos[0]["quality"], "")

    def test_parse_multiple_blocks(self):
        html = """
        <div id="video_aaaa" data-id="1" data-eid="eid1"
             class="frame-block thumb-block">
        <div class="thumb-under"><p class="title"><a href="#" title="Video 1">
        Video 1 <span class="duration">10 min</span></a></p>
        <p class="metadata"><span class="bg"><a href="/u1"><span class="name">U1</span></a></span></p></div>
        </div>
        <div id="video_bbbb" data-id="2" data-eid="eid2"
             class="frame-block thumb-block">
        <div class="thumb-under"><p class="title"><a href="#" title="Video 2">
        Video 2 <span class="duration">20 min</span></a></p>
        <p class="metadata"><span class="bg"><a href="/u2"><span class="name">U2</span></a></span></p></div>
        </div>
        """
        videos = xv_spider._parse_video_blocks(html)
        self.assertEqual(len(videos), 2)
        self.assertEqual(videos[0]["eid"], "eid1")
        self.assertEqual(videos[1]["eid"], "eid2")

    def test_parse_views_millions(self):
        html = """
        <div id="video_kkkk" data-id="99" data-eid="eid99"
             class="frame-block thumb-block">
        <div class="thumb-under"><p class="title"><a href="#" title="Big">
        Big <span class="duration">30 min</span></a></p>
        <p class="metadata"><span class="bg"><span class="duration">30 min</span>
        <a href="/u"><span class="name">Uploader</span></a>
        <span>8.8M Views</span></span></p></div>
        </div>
        """
        videos = xv_spider._parse_video_blocks(html)
        self.assertEqual(len(videos), 1)
        self.assertEqual(videos[0]["views"], "8.8M views")

    def test_parse_empty_blocks(self):
        videos = xv_spider._parse_video_blocks("<html></html>")
        self.assertEqual(videos, [])


class TestConfigLoading(unittest.TestCase):
    def setUp(self):
        self.original = xv_spider.XV_CONFIG_FILE
        self.tmpdir = tempfile.TemporaryDirectory()
        xv_spider.XV_CONFIG_FILE = Path(self.tmpdir.name) / "xvideos.json"

    def tearDown(self):
        xv_spider.XV_CONFIG_FILE = self.original
        self.tmpdir.cleanup()

    def test_load_valid_config(self):
        config = {"sources": [{"type": "category", "id": "Lingerie-83", "tag": "test"}]}
        xv_spider.XV_CONFIG_FILE.write_text(json.dumps(config))
        sources = xv_spider.load_sources()
        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0]["id"], "Lingerie-83")

    def test_load_missing_config(self):
        sources = xv_spider.load_sources()
        self.assertEqual(sources, [])


class TestEidDedup(unittest.TestCase):
    def setUp(self):
        self.original = xv_spider.XV_VIDEOS_FILE
        self.tmpdir = tempfile.TemporaryDirectory()
        xv_spider.XV_DIR = Path(self.tmpdir.name)
        xv_spider.XV_VIDEOS_FILE = xv_spider.XV_DIR / "videos.jsonl"
        xv_spider.XV_DIR.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        xv_spider.XV_VIDEOS_FILE = self.original
        self.tmpdir.cleanup()

    def test_load_empty_eids(self):
        eids = xv_spider.load_existing_eids()
        self.assertEqual(eids, set())

    def test_load_existing_eids(self):
        xv_spider.XV_VIDEOS_FILE.write_text(
            '{"eid":"abc123","title":"Test"}\n{"eid":"def456","title":"Test2"}\n'
        )
        eids = xv_spider.load_existing_eids()
        self.assertEqual(eids, {"abc123", "def456"})


class TestAppendVideos(unittest.TestCase):
    def setUp(self):
        self.original = xv_spider.XV_VIDEOS_FILE
        self.tmpdir = tempfile.TemporaryDirectory()
        xv_spider.XV_DIR = Path(self.tmpdir.name)
        xv_spider.XV_VIDEOS_FILE = xv_spider.XV_DIR / "videos.jsonl"
        xv_spider.XV_DIR.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        xv_spider.XV_VIDEOS_FILE = self.original
        self.tmpdir.cleanup()

    def test_append_creates_file(self):
        xv_spider._append_videos([{"eid": "test1", "title": "T1"}])
        self.assertTrue(xv_spider.XV_VIDEOS_FILE.exists())
        lines = xv_spider.XV_VIDEOS_FILE.read_text().strip().split("\n")
        self.assertEqual(len(lines), 1)

    def test_append_preserves_existing(self):
        xv_spider.XV_VIDEOS_FILE.write_text('{"eid":"old","title":"Old"}\n')
        xv_spider._append_videos([{"eid": "new", "title": "New"}])
        lines = xv_spider.XV_VIDEOS_FILE.read_text().strip().split("\n")
        self.assertEqual(len(lines), 2)


if __name__ == "__main__":
    unittest.main()
