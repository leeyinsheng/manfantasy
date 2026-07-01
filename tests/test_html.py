"""Integration test: validates generated HTML structure and file references."""
import sys
import json
import unittest
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import tg_core as mod
import generate_html


class TestGenerateHtml(unittest.TestCase):
    def setUp(self):
        self.original_download = mod.DOWNLOAD_DIR
        self.tmpdir = tempfile.TemporaryDirectory()
        mod.DOWNLOAD_DIR = Path(self.tmpdir.name)
        for ch_id in ("ai_guoman", "dashijian"):
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

    def tearDown(self):
        mod.DOWNLOAD_DIR = self.original_download
        self.tmpdir.cleanup()

    def _read_html(self):
        out = mod.DOWNLOAD_DIR / "index.html"
        with open(out, encoding="utf-8") as f:
            return f.read()

    def test_html_generated_without_error(self):
        result = generate_html.generate()
        self.assertIsNotNone(result)

    def test_html_contains_tabs(self):
        generate_html.generate()
        html = self._read_html()
        self.assertIn("男人的幻想", html)
        self.assertIn("東南亞大事件", html)

    def test_html_has_tab_content(self):
        generate_html.generate()
        html = self._read_html()
        self.assertIn("tab-ai_guoman", html)
        self.assertIn("tab-dashijian", html)
        self.assertIn("tab-content active", html)

    def test_media_paths_start_with_channel_id(self):
        generate_html.generate()
        html = self._read_html()
        import re
        srcs = re.findall(r'src="([^"]+)"', html)
        for src in srcs:
            parts = src.split("/")
            self.assertIn(parts[0], ("ai_guoman", "dashijian"),
                          f"Path '{src}' does not start with channel ID")

    def test_news_card_has_text_and_media(self):
        generate_html.generate()
        html = self._read_html()
        self.assertIn("Test news", html)
        self.assertIn("card-date", html)
        self.assertIn("card-text", html)

    def test_empty_channel_shows_placeholder(self):
        msg_file = mod.DOWNLOAD_DIR / "dashijian" / "messages.jsonl"
        msg_file.write_text("", encoding="utf-8")
        generate_html.generate()
        html = self._read_html()
        self.assertIn("尚無內容", html)

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


if __name__ == "__main__":
    unittest.main()
