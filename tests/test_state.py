"""
Tests for configuration, state I/O, and v2 channel/message functions.
"""
import sys
import json
import unittest
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import tg_core as mod


CHANNEL_ID = "test_ch"


class TestLoadConfig(unittest.TestCase):
    def setUp(self):
        self.original = mod.CONFIG_FILE

    def tearDown(self):
        mod.CONFIG_FILE = self.original

    def test_returns_empty_dict_when_file_missing(self):
        mod.CONFIG_FILE = Path(tempfile.gettempdir()) / "nonexistent_config.json"
        result = mod.load_config()
        self.assertEqual(result, {})

    def test_loads_valid_json(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"api_id": 123, "api_hash": "abc"}, f)
            temp_path = Path(f.name)
        try:
            mod.CONFIG_FILE = temp_path
            result = mod.load_config()
            self.assertEqual(result, {"api_id": 123, "api_hash": "abc"})
        finally:
            temp_path.unlink()

    def test_returns_empty_dict_on_corrupted_json(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{not valid json")
            temp_path = Path(f.name)
        try:
            mod.CONFIG_FILE = temp_path
            result = mod.load_config()
            self.assertEqual(result, {})
        finally:
            temp_path.unlink()


class TestLoadState(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.original_download = mod.DOWNLOAD_DIR
        mod.DOWNLOAD_DIR = Path(self.tmpdir.name)

    def tearDown(self):
        mod.DOWNLOAD_DIR = self.original_download
        self.tmpdir.cleanup()

    def test_returns_empty_set_when_file_missing(self):
        result = mod.load_state(CHANNEL_ID)
        self.assertEqual(result, set())

    def test_loads_sorted_id_list_as_set(self):
        state_file = mod.get_state_file(CHANNEL_ID)
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(json.dumps([1003, 1001, 1002]))
        result = mod.load_state(CHANNEL_ID)
        self.assertEqual(result, {1001, 1002, 1003})

    def test_returns_empty_set_on_corrupted_json(self):
        state_file = mod.get_state_file(CHANNEL_ID)
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text("[1, 2, broken")
        result = mod.load_state(CHANNEL_ID)
        self.assertEqual(result, set())

    def test_returns_empty_set_on_non_list_json(self):
        state_file = mod.get_state_file(CHANNEL_ID)
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(json.dumps({"ids": [1, 2]}))
        result = mod.load_state(CHANNEL_ID)
        self.assertEqual(result, set())


class TestSaveState(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.original_download = mod.DOWNLOAD_DIR
        mod.DOWNLOAD_DIR = Path(self.tmpdir.name)

    def tearDown(self):
        mod.DOWNLOAD_DIR = self.original_download
        self.tmpdir.cleanup()

    def test_saves_state_as_sorted_json(self):
        mod.save_state(CHANNEL_ID, {1003, 1001, 1002})
        loaded = json.loads(mod.get_state_file(CHANNEL_ID).read_text())
        self.assertEqual(loaded, [1001, 1002, 1003])

    def test_creates_parent_directory(self):
        mod.save_state(CHANNEL_ID, {42})
        self.assertTrue(mod.get_state_file(CHANNEL_ID).exists())


class TestMessageStore(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.original_download = mod.DOWNLOAD_DIR
        mod.DOWNLOAD_DIR = Path(self.tmpdir.name)

    def tearDown(self):
        mod.DOWNLOAD_DIR = self.original_download
        self.tmpdir.cleanup()

    def test_append_and_load_messages(self):
        mod.append_message_record(CHANNEL_ID, {"id": 1, "text": "第一條", "channel": CHANNEL_ID})
        mod.append_message_record(CHANNEL_ID, {"id": 2, "text": "第二條", "channel": CHANNEL_ID})
        records = mod.load_messages(CHANNEL_ID)
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["text"], "第一條")
        self.assertEqual(records[1]["text"], "第二條")

    def test_load_messages_empty_when_no_file(self):
        records = mod.load_messages("nonexistent")
        self.assertEqual(records, [])

    def test_load_messages_skips_corrupted_lines(self):
        messages_file = mod.get_messages_file(CHANNEL_ID)
        messages_file.parent.mkdir(parents=True, exist_ok=True)
        messages_file.write_text('{"id":1}\n{broken\n{"id":2}\n', encoding="utf-8")
        records = mod.load_messages(CHANNEL_ID)
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["id"], 1)
        self.assertEqual(records[1]["id"], 2)


class TestChannelDir(unittest.TestCase):
    def test_get_channel_dir_returns_correct_path(self):
        d = mod.get_channel_dir("my_channel")
        self.assertEqual(d.name, "my_channel")
        self.assertIn("download", str(d))

    def test_get_photo_dir(self):
        d = mod.get_photo_dir("my_channel")
        self.assertEqual(d.name, "photo")

    def test_get_video_dir(self):
        d = mod.get_video_dir("my_channel")
        self.assertEqual(d.name, "video")


if __name__ == "__main__":
    unittest.main()
