"""Unit tests for xv_pipeline.py — pipeline orchestration, pending entry detection."""
import json
import sys
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import xv_pipeline


class TestGetPendingEntries(unittest.TestCase):
    def setUp(self):
        self.original_file = xv_pipeline.XV_VIDEOS_FILE
        self.tmpdir = tempfile.TemporaryDirectory()
        xv_pipeline.XV_DIR = Path(self.tmpdir.name)
        xv_pipeline.XV_VIDEOS_FILE = xv_pipeline.XV_DIR / "videos.jsonl"

    def tearDown(self):
        xv_pipeline.XV_VIDEOS_FILE = self.original_file
        self.tmpdir.cleanup()

    def test_no_file_returns_empty(self):
        entries = xv_pipeline.get_pending_entries()
        self.assertEqual(entries, [])

    def test_all_downloaded_returns_empty(self):
        data = [
            {"eid": "aaa", "media_path": "https://oss.test/aaa.mp4"},
            {"eid": "bbb", "media_path": "https://oss.test/bbb.mp4"},
        ]
        xv_pipeline.XV_DIR.mkdir(parents=True, exist_ok=True)
        with open(xv_pipeline.XV_VIDEOS_FILE, "w", encoding="utf-8") as f:
            for e in data:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
        entries = xv_pipeline.get_pending_entries()
        self.assertEqual(entries, [])

    def test_returns_only_pending(self):
        data = [
            {"eid": "aaa", "media_path": "https://oss.test/aaa.mp4", "title": "A"},
            {"eid": "bbb", "title": "B"},
            {"eid": "ccc", "media_path": "https://oss.test/ccc.mp4", "title": "C"},
            {"eid": "ddd", "title": "D"},
        ]
        xv_pipeline.XV_DIR.mkdir(parents=True, exist_ok=True)
        with open(xv_pipeline.XV_VIDEOS_FILE, "w", encoding="utf-8") as f:
            for e in data:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
        entries = xv_pipeline.get_pending_entries()
        self.assertEqual(len(entries), 2)
        eids = [e["eid"] for e in entries]
        self.assertIn("bbb", eids)
        self.assertIn("ddd", eids)


class TestBuildVideoUrl(unittest.TestCase):
    def test_builds_url_from_eid_and_video_id(self):
        url = xv_pipeline.build_video_url({"eid": "abc123", "video_id": 98765})
        self.assertEqual(url, "https://www.xvideos.com/video.abc123/98765/")

    def test_builds_url_without_video_id(self):
        url = xv_pipeline.build_video_url({"eid": "abc123"})
        self.assertEqual(url, "https://www.xvideos.com/video.abc123/")

    def test_empty_eid(self):
        url = xv_pipeline.build_video_url({"eid": ""})
        self.assertEqual(url, "https://www.xvideos.com/video./")


class TestUpdateEntry(unittest.TestCase):
    def setUp(self):
        self.original_file = xv_pipeline.XV_VIDEOS_FILE
        self.tmpdir = tempfile.TemporaryDirectory()
        xv_pipeline.XV_DIR = Path(self.tmpdir.name)
        xv_pipeline.XV_VIDEOS_FILE = xv_pipeline.XV_DIR / "videos.jsonl"

    def tearDown(self):
        xv_pipeline.XV_VIDEOS_FILE = self.original_file
        self.tmpdir.cleanup()

    def test_updates_existing_entry(self):
        data = [
            {"eid": "aaa", "media_path": "https://oss.test/aaa.mp4"},
            {"eid": "bbb", "title": "B"},
            {"eid": "ccc", "title": "C"},
        ]
        xv_pipeline.XV_DIR.mkdir(parents=True, exist_ok=True)
        with open(xv_pipeline.XV_VIDEOS_FILE, "w", encoding="utf-8") as f:
            for e in data:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")

        xv_pipeline.update_entry("bbb", media_path="https://oss.test/bbb.mp4")

        with open(xv_pipeline.XV_VIDEOS_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        entries = [json.loads(l) for l in lines if l.strip()]
        for e in entries:
            if e["eid"] == "aaa":
                self.assertEqual(e["media_path"], "https://oss.test/aaa.mp4")
            elif e["eid"] == "bbb":
                self.assertEqual(e["media_path"], "https://oss.test/bbb.mp4")
            elif e["eid"] == "ccc":
                self.assertNotIn("media_path", e)

    def test_update_nonexistent_no_error(self):
        xv_pipeline.XV_DIR.mkdir(parents=True, exist_ok=True)
        xv_pipeline.XV_VIDEOS_FILE.write_text('{"eid":"aaa"}\n')
        xv_pipeline.update_entry("nonexistent", media_path="x")
        lines = xv_pipeline.XV_VIDEOS_FILE.read_text().strip().split("\n")
        self.assertEqual(len(lines), 1)


class TestRunPipeline(unittest.TestCase):
    @patch("xv_pipeline.xv_spider.crawl", return_value=5)
    @patch("xv_pipeline.download_pending")
    def test_pipeline_calls_spider_then_download(self, mock_dl, mock_crawl):
        xv_pipeline.run_pipeline(max_downloads=10)
        mock_crawl.assert_called_once()
        mock_dl.assert_called_once_with(max_downloads=10)

    @patch("xv_pipeline.xv_spider.crawl", return_value=0)
    @patch("xv_pipeline.download_pending")
    def test_pipeline_works_with_zero_new(self, mock_dl, mock_crawl):
        xv_pipeline.run_pipeline(max_downloads=5)
        mock_crawl.assert_called_once()
        mock_dl.assert_called_once_with(max_downloads=5)


if __name__ == "__main__":
    unittest.main()
