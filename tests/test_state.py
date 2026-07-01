"""
Tests for configuration and state file I/O.
"""
import sys
import json
import unittest
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import tg_core as mod


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


class TestLoadState(unittest.TestCase):
    def setUp(self):
        self.original = mod.STATE_FILE

    def tearDown(self):
        mod.STATE_FILE = self.original

    def test_returns_empty_set_when_file_missing(self):
        mod.STATE_FILE = Path(tempfile.gettempdir()) / "nonexistent_state.json"
        result = mod.load_state()
        self.assertEqual(result, set())

    def test_loads_sorted_id_list_as_set(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump([1003, 1001, 1002], f)
            temp_path = Path(f.name)
        try:
            mod.STATE_FILE = temp_path
            result = mod.load_state()
            self.assertEqual(result, {1001, 1002, 1003})
        finally:
            temp_path.unlink()

    def test_loads_empty_array_as_empty_set(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump([], f)
            temp_path = Path(f.name)
        try:
            mod.STATE_FILE = temp_path
            result = mod.load_state()
            self.assertEqual(result, set())
        finally:
            temp_path.unlink()


class TestSaveState(unittest.TestCase):
    def setUp(self):
        self.original = mod.STATE_FILE

    def tearDown(self):
        mod.STATE_FILE = self.original

    def test_saves_state_as_sorted_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / ".downloaded_state.json"
            mod.STATE_FILE = state_path
            mod.save_state({1003, 1001, 1002})
            loaded = json.loads(state_path.read_text())
            self.assertEqual(loaded, [1001, 1002, 1003])

    def test_creates_parent_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / "subdir" / ".downloaded_state.json"
            mod.STATE_FILE = state_path
            mod.save_state({42})
            self.assertTrue(state_path.exists())
            self.assertTrue(state_path.parent.exists())
            loaded = json.loads(state_path.read_text())
            self.assertEqual(loaded, [42])


if __name__ == "__main__":
    unittest.main()
