"""Integration test: validates v5 APP mode HTML structure, embedded data, plus xvideos."""
import json
import re
import sys
import unittest
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import tg_core as mod
import generate_html
import xv_spider


class TestGenerateHtml(unittest.TestCase):
    def setUp(self):
        self.original_download = mod.DOWNLOAD_DIR
        self.original_channels = mod.CHANNELS_FILE
        self.tmpdir = tempfile.TemporaryDirectory()
        mod.DOWNLOAD_DIR = Path(self.tmpdir.name)

        for ch_id in ("ai_guoman", "ciyuanb", "llcosfc", "dashijian"):
            (mod.DOWNLOAD_DIR / ch_id / "photo").mkdir(parents=True, exist_ok=True)
            (mod.DOWNLOAD_DIR / ch_id / "video").mkdir(parents=True, exist_ok=True)

        (mod.DOWNLOAD_DIR / "ai_guoman" / "photo" / "test_photo.jpg").write_text("")
        (mod.DOWNLOAD_DIR / "ai_guoman" / "video" / "test_video.mp4").write_text("")

        msg_file = mod.DOWNLOAD_DIR / "dashijian" / "messages.jsonl"
        msg_file.write_text(
            json.dumps({"id": 1, "date": "2025-07-01T12:00:00", "text": "Test news",
                        "channel": "dashijian",
                        "media": [{"type": "photo", "path": "photo/test_news.jpg"}]},
                       ensure_ascii=False) + "\n",
            encoding="utf-8"
        )

        self._tmp_channels = self.tmpdir.name + "/_channels.json"
        mod.CHANNELS_FILE = Path(self._tmp_channels)
        self._write_test_channels()

    def _write_test_channels(self):
        channels = {
            "channels": [
                {"id": "ai_guoman", "username": "AIguoman18", "name": "異想空間",
                 "mode": "text", "group": "mens_fantasy", "fetch_limit": 50},
                {"id": "dashijian", "username": "dashijian", "name": "東南亞大事件",
                 "mode": "text", "fetch_limit": 50},
            ]
        }
        Path(self._tmp_channels).write_text(json.dumps(channels), encoding="utf-8")

    def tearDown(self):
        mod.DOWNLOAD_DIR = self.original_download
        mod.CHANNELS_FILE = self.original_channels
        self.tmpdir.cleanup()

    def _read_html(self):
        out = mod.DOWNLOAD_DIR / "index.html"
        with open(out, encoding="utf-8") as f:
            return f.read()

    def _extract_json_data(self, html):
        m = re.search(r"window\.__DATA__\s*=\s*(\{.*?\});", html, re.DOTALL)
        if m:
            return json.loads(m.group(1))
        return {}

    def test_html_generated_without_error(self):
        result = generate_html.generate()
        self.assertIsNotNone(result)

    def test_html_contains_tabs(self):
        generate_html.generate()
        html = self._read_html()
        self.assertIn("異想空間", html)
        self.assertIn("大事件", html)

    def test_html_has_app_structure(self):
        generate_html.generate()
        html = self._read_html()
        self.assertIn("app-shell", html)
        self.assertIn("app-header", html)
        self.assertIn("bottom-nav", html)
        self.assertIn("nav-item", html)
        self.assertIn("tab-content active", html)

    def test_badge_counts_embedded(self):
        generate_html.generate()
        html = self._read_html()
        self.assertIn("__DATA__", html)

    def test_news_data_in_json(self):
        generate_html.generate()
        html = self._read_html()
        data = self._extract_json_data(html)
        self.assertIn("dashijian", data)
        msgs = data["dashijian"]["messages"]
        self.assertGreaterEqual(len(msgs), 1)
        self.assertEqual(msgs[0]["text"], "Test news")
        self.assertIn("media", msgs[0])

    def test_media_paths_in_json_start_with_channel_id(self):
        generate_html.generate()
        html = self._read_html()
        data = self._extract_json_data(html)
        for tab_id, tab in data.items():
            for msg in tab.get("messages", []):
                for media in msg.get("media", []):
                    self.assertIn("/", media["path"],
                        f"Path '{media['path']}' in tab {tab_id} missing channel_id prefix")

    def test_html_is_valid_structure(self):
        generate_html.generate()
        html = self._read_html()
        self.assertTrue(html.startswith("<!DOCTYPE html>"))
        self.assertIn("<html", html)
        self.assertIn("</html>", html)
        self.assertIn("<style>", html)
        self.assertIn("</style>", html)
        self.assertIn("<script>", html)
        self.assertIn("</script>", html)

    def test_lightbox_html_present(self):
        generate_html.generate()
        html = self._read_html()
        self.assertIn("lightbox", html)
        self.assertIn("lb-close", html)
        self.assertIn("lb-prev", html)
        self.assertIn("lb-next", html)
        self.assertIn("lb-counter", html)

    def test_pagination_present(self):
        generate_html.generate()
        html = self._read_html()
        self.assertIn("pagination", html)
        self.assertIn("page-btn", html)

    def test_channel_group_produces_merged_tab(self):
        generate_html.generate()
        html = self._read_html()
        data = self._extract_json_data(html)
        self.assertIn("mens_fantasy", data)
        self.assertEqual(data["mens_fantasy"]["name"], "異想空間")

    def test_card_structure_in_json(self):
        generate_html.generate()
        html = self._read_html()
        data = self._extract_json_data(html)
        for tab_id, tab in data.items():
            for msg in tab.get("messages", []):
                self.assertIn("id", msg)
                self.assertIn("date", msg)
                self.assertIn("text", msg)
                self.assertIn("channel", msg)

    def test_empty_tab_json_structure(self):
        generate_html.generate()
        html = self._read_html()
        data = self._extract_json_data(html)
        self.assertIn("mens_fantasy", data)
        self.assertIn("messages", data["mens_fantasy"])
        self.assertIn("total", data["mens_fantasy"])


class TestXvHtml(unittest.TestCase):
    def setUp(self):
        self.original_download = mod.DOWNLOAD_DIR
        self.original_channels = mod.CHANNELS_FILE
        self.original_xv_file = generate_html.XV_VIDEOS_FILE
        self.tmpdir = tempfile.TemporaryDirectory()
        mod.DOWNLOAD_DIR = Path(self.tmpdir.name)
        (mod.DOWNLOAD_DIR / "xvideos").mkdir(parents=True, exist_ok=True)

        for ch_id in ("ai_guoman", "ciyuanb", "llcosfc", "dashijian"):
            (mod.DOWNLOAD_DIR / ch_id / "photo").mkdir(parents=True, exist_ok=True)
            (mod.DOWNLOAD_DIR / ch_id / "video").mkdir(parents=True, exist_ok=True)

        msg_file = mod.DOWNLOAD_DIR / "dashijian" / "messages.jsonl"
        msg_file.write_text(
            json.dumps({"id": 1, "date": "2025-07-01T12:00:00", "text": "Test news",
                        "channel": "dashijian",
                        "media": [{"type": "photo", "path": "photo/test_news.jpg"}]},
                       ensure_ascii=False) + "\n",
            encoding="utf-8"
        )

        self._tmp_channels = self.tmpdir.name + "/_channels.json"
        mod.CHANNELS_FILE = Path(self._tmp_channels)
        self._write_test_channels()

        xv_file = mod.DOWNLOAD_DIR / "xvideos" / "videos.jsonl"
        xv_videos = [
            {"eid": "eid1", "video_id": 1, "title": "Test Video 1", "duration": "10 min",
             "views": "1k views", "uploader": "TestUser", "thumbnail": "http://thumb/1.jpg",
             "quality": "1080p", "tags": ["內衣絲襪"], "fetched_at": "2026-07-03T12:00:00"},
            {"eid": "eid2", "video_id": 2, "title": "Test Video 2", "duration": "20 min",
             "views": "2k views", "uploader": "TestUser2", "thumbnail": "http://thumb/2.jpg",
             "quality": "720p", "tags": ["日本"], "fetched_at": "2026-07-03T11:00:00"},
        ]
        xv_file.write_text(
            "\n".join(json.dumps(v, ensure_ascii=False) for v in xv_videos),
            encoding="utf-8"
        )
        generate_html.XV_VIDEOS_FILE = xv_file

    def _write_test_channels(self):
        channels = {
            "channels": [
                {"id": "ai_guoman", "username": "AIguoman18", "name": "男人的幻想",
                 "mode": "text", "group": "mens_fantasy", "fetch_limit": 50},
                {"id": "dashijian", "username": "dashijian", "name": "東南亞大事件",
                 "mode": "text", "fetch_limit": 50},
            ]
        }
        Path(self._tmp_channels).write_text(json.dumps(channels), encoding="utf-8")

    def tearDown(self):
        mod.DOWNLOAD_DIR = self.original_download
        mod.CHANNELS_FILE = self.original_channels
        generate_html.XV_VIDEOS_FILE = self.original_xv_file
        self.tmpdir.cleanup()

    def _read_html(self):
        out = mod.DOWNLOAD_DIR / "index.html"
        with open(out, encoding="utf-8") as f:
            return f.read()

    def test_xv_tab_present(self):
        generate_html.generate()
        html = self._read_html()
        self.assertIn("弟兄們", html)
        self.assertIn("content-xvideos", html)

    def test_xv_data_embedded(self):
        generate_html.generate()
        html = self._read_html()
        self.assertIn("__XV_DATA__", html)

    def test_xv_data_content(self):
        generate_html.generate()
        html = self._read_html()
        m = re.search(r"window\.__XV_DATA__\s*=\s*(\{.*?\});", html, re.DOTALL)
        self.assertIsNotNone(m)
        data = json.loads(m.group(1))
        self.assertIn("videos", data)
        self.assertEqual(len(data["videos"]), 2)
        self.assertEqual(data["videos"][0]["eid"], "eid1")

    def test_xv_tag_bar_present(self):
        generate_html.generate()
        html = self._read_html()
        self.assertIn("tag-bar", html)
        self.assertIn("tag-btn", html)
        self.assertIn("內衣絲襪", html)
        self.assertIn("日本", html)

    def test_xv_embed_container(self):
        generate_html.generate()
        html = self._read_html()
        self.assertIn("xv-embed", html)
        self.assertIn("data-eid", html)

    def test_xv_tab_no_search_bar(self):
        generate_html.generate()
        html = self._read_html()
        tab_xv_match = re.search(
            r'<div class="tab-content(?: active)?" id="content-xvideos".*?</nav>',
            html, re.DOTALL
        )
        if tab_xv_match:
            xv_section = tab_xv_match.group(0)
            self.assertNotIn("search-bar", xv_section)

    def test_existing_tabs_unaffected(self):
        generate_html.generate()
        html = self._read_html()
        self.assertIn("大事件", html)
        self.assertIn("bottom-nav", html)
        self.assertIn("content-mens_fantasy", html)

    def test_xv_pagination_present(self):
        generate_html.generate()
        html = self._read_html()
        self.assertIn("pagination-xvideos", html)


if __name__ == "__main__":
    unittest.main()
