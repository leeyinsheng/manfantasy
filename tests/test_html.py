"""Integration test: validates v3 HTML structure, embedded data, and new components."""
import json
import re
import sys
import unittest
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import tg_core as mod
import generate_html


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
        self.assertIn("男人的幻想", html)
        self.assertIn("東南亞大事件", html)

    def test_html_has_tab_content_v3(self):
        generate_html.generate()
        html = self._read_html()
        self.assertIn("tab-mens_fantasy", html)
        self.assertIn("tab-dashijian", html)
        self.assertIn("tab-content active", html)

    def test_badge_counts_embedded(self):
        generate_html.generate()
        html = self._read_html()
        self.assertIn("badge", html)

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

    def test_search_bar_present(self):
        generate_html.generate()
        html = self._read_html()
        self.assertIn("search-bar", html)
        self.assertIn("search-input", html)
        self.assertIn("time-presets", html)
        self.assertIn("preset-btn", html)
        self.assertIn("result-count", html)

    def test_load_more_present(self):
        generate_html.generate()
        html = self._read_html()
        self.assertIn("load-more-wrap", html)
        self.assertIn("load-more-btn", html)

    def test_channel_group_produces_merged_tab(self):
        generate_html.generate()
        html = self._read_html()
        data = self._extract_json_data(html)
        self.assertIn("mens_fantasy", data)
        self.assertEqual(data["mens_fantasy"]["name"], "男人的幻想")

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


if __name__ == "__main__":
    unittest.main()
