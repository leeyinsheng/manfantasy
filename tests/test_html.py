"""Integration test: validates v7 waterfall HTML structure and embedded data."""
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
                       ensure_ascii=False) + "\n"
            + json.dumps({"id": 2, "date": "2025-07-02T09:00:00", "text": "Text-only news",
                        "channel": "dashijian", "media": []},
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
                 "mode": "text", "group": "news", "fetch_limit": 50},
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

    def test_html_has_tab_content(self):
        generate_html.generate()
        html = self._read_html()
        self.assertIn("tab-mens_fantasy", html)
        self.assertIn("tab-news", html)
        self.assertIn("tab-content active", html)

    def test_news_data_in_json(self):
        generate_html.generate()
        html = self._read_html()
        data = self._extract_json_data(html)
        self.assertIn("news", data)
        msgs = data["news"]["messages"]
        self.assertGreaterEqual(len(msgs), 1)
        photo_msg = next(m for m in msgs if m["text"] == "Test news")
        self.assertIn("media", photo_msg)

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

    def test_viewport_mobile_only(self):
        generate_html.generate()
        html = self._read_html()
        self.assertIn('name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"', html)

    def test_app_shell_present(self):
        generate_html.generate()
        html = self._read_html()
        self.assertIn('class="app"', html)
        self.assertIn('class="app-header"', html)
        self.assertIn('class="app-content"', html)

    def test_bottom_nav_present(self):
        generate_html.generate()
        html = self._read_html()
        self.assertIn("bottom-nav", html)
        self.assertIn("nav-item", html)
        self.assertIn('data-tab="mens_fantasy"', html)
        self.assertIn("🏠", html)
        self.assertIn("📰", html)

    def test_no_top_tab_bar(self):
        generate_html.generate()
        html = self._read_html()
        self.assertNotIn("tab-nav", html)
        self.assertNotIn("tab-btn", html)

    def test_waterfall_columns_present(self):
        generate_html.generate()
        html = self._read_html()
        self.assertIn("wfcol-mens_fantasy-0", html)
        self.assertIn("wfcol-mens_fantasy-1", html)
        self.assertIn("textonly-mens_fantasy", html)

    def test_sentinel_present_no_pagination(self):
        generate_html.generate()
        html = self._read_html()
        self.assertIn("sentinel-mens_fantasy", html)
        self.assertNotIn("pagination", html)
        self.assertNotIn("page-btn", html)

    def test_lightbox_html_present(self):
        generate_html.generate()
        html = self._read_html()
        self.assertIn("lightbox", html)
        self.assertIn("lb-close", html)
        self.assertIn("lb-prev", html)
        self.assertIn("lb-next", html)
        self.assertIn("lb-counter", html)

    def test_detail_sheet_present(self):
        generate_html.generate()
        html = self._read_html()
        self.assertIn("sheet-backdrop", html)
        self.assertIn("sheet-close", html)
        self.assertIn("sheet-body", html)

    def test_search_panel_present(self):
        generate_html.generate()
        html = self._read_html()
        self.assertIn("search-panel-mens_fantasy", html)
        self.assertIn("search-input", html)
        self.assertIn("time-presets", html)
        self.assertIn("preset-btn", html)
        self.assertIn("result-count", html)
        self.assertIn("search-toggle", html)

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

    def test_text_only_message_has_empty_media(self):
        generate_html.generate()
        html = self._read_html()
        data = self._extract_json_data(html)
        msgs = data["news"]["messages"]
        text_only = [m for m in msgs if m["text"] == "Text-only news"]
        self.assertEqual(len(text_only), 1)
        self.assertEqual(text_only[0]["media"], [])

    def test_default_icon_for_unmapped_group(self):
        mod.CHANNELS_FILE.write_text(json.dumps({
            "channels": [
                {"id": "misc_ch", "username": "misc", "name": "雜項",
                 "mode": "text", "group": "misc", "fetch_limit": 50},
            ]
        }), encoding="utf-8")
        generate_html.generate()
        html = self._read_html()
        self.assertIn(generate_html.DEFAULT_ICON, html)


class TestXvideoTab(unittest.TestCase):
    def setUp(self):
        self.original_download = mod.DOWNLOAD_DIR
        self.original_channels = mod.CHANNELS_FILE
        self.tmpdir = tempfile.TemporaryDirectory()
        mod.DOWNLOAD_DIR = Path(self.tmpdir.name)

        for ch_id in ("ai_guoman", "dashijian"):
            (mod.DOWNLOAD_DIR / ch_id / "photo").mkdir(parents=True, exist_ok=True)
            (mod.DOWNLOAD_DIR / ch_id / "video").mkdir(parents=True, exist_ok=True)

        self._tmp_channels = self.tmpdir.name + "/_channels.json"
        mod.CHANNELS_FILE = Path(self._tmp_channels)
        mod.CHANNELS_FILE.write_text(json.dumps({
            "channels": [
                {"id": "ai_guoman", "username": "AIguoman18", "name": "男人的幻想",
                 "mode": "text", "group": "mens_fantasy", "fetch_limit": 50},
            ]
        }), encoding="utf-8")

        xv_dir = mod.DOWNLOAD_DIR / "xvideos"
        xv_dir.mkdir(parents=True, exist_ok=True)
        (xv_dir / "videos.jsonl").write_text(
            json.dumps({"eid": "eid001", "video_id": 12345, "title": "Test Video",
                        "duration": "12:34", "thumbnail": "https://img.test/1.jpg",
                        "fetched_at": "2025-07-01T12:00:00"},
                       ensure_ascii=False) + "\n"
            + json.dumps({"eid": "eid002", "video_id": 67890, "title": "Test Video 2",
                        "duration": "8:15", "thumbnail": "https://img.test/2.jpg",
                        "fetched_at": "2025-07-02T09:00:00"},
                       ensure_ascii=False) + "\n",
            encoding="utf-8"
        )

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

    def test_xvideo_tab_in_html(self):
        generate_html.generate()
        html = self._read_html()
        self.assertIn("xvideo", html)
        self.assertIn("tab-xvideo", html)
        self.assertIn("❌", html)

    def test_xvideo_tab_in_nav(self):
        generate_html.generate()
        html = self._read_html()
        self.assertIn('data-tab="xvideo"', html)
        self.assertIn('aria-label="xvideo"', html)

    def test_xvideo_in_embedded_data(self):
        generate_html.generate()
        html = self._read_html()
        data = self._extract_json_data(html)
        self.assertIn("xvideo", data)
        self.assertEqual(len(data["xvideo"]["messages"]), 2)

    def test_xvideo_message_has_xv_flag(self):
        generate_html.generate()
        html = self._read_html()
        data = self._extract_json_data(html)
        for msg in data["xvideo"]["messages"]:
            self.assertTrue(msg["_xv"])
            self.assertIn("video_id", msg)
            self.assertIn("thumbnail", msg)
            self.assertIn("duration", msg)

    def test_xvideo_nav_icon_only_no_text_label(self):
        generate_html.generate()
        html = self._read_html()
        self.assertNotIn('<span class="label">', html)

    def test_xvideo_nav_has_active_indicator(self):
        generate_html.generate()
        html = self._read_html()
        self.assertIn(".nav-item::after", html)

    def test_xvideo_card_has_badge_duration_css(self):
        generate_html.generate()
        html = self._read_html()
        self.assertIn("badge-duration", html)

    def test_xvideo_embed_css_present(self):
        generate_html.generate()
        html = self._read_html()
        self.assertIn("xv-embed", html)

    def test_lightbox_embed_function_in_js(self):
        generate_html.generate()
        html = self._read_html()
        self.assertIn("openLbEmbed", html)
        self.assertIn("embedframe", html)

    def test_no_text_label_in_nav_items(self):
        generate_html.generate()
        html = self._read_html()
        self.assertNotIn('class="label"', html)

    def test_xvideo_messages_sorted_by_date(self):
        generate_html.generate()
        html = self._read_html()
        data = self._extract_json_data(html)
        msgs = data["xvideo"]["messages"]
        self.assertEqual(msgs[0]["text"], "Test Video 2")
        self.assertEqual(msgs[1]["text"], "Test Video")


if __name__ == "__main__":
    unittest.main()
