"""Unit tests for oss_uploader.py."""
import json
import sys
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import oss_uploader


class TestOssConfig(unittest.TestCase):
    def setUp(self):
        self.original = oss_uploader.OSS_CONFIG_FILE
        self.tmpdir = tempfile.TemporaryDirectory()
        oss_uploader.OSS_CONFIG_FILE = Path(self.tmpdir.name) / "oss_config.json"

    def tearDown(self):
        oss_uploader.OSS_CONFIG_FILE = self.original
        self.tmpdir.cleanup()

    def _write_config(self, data):
        oss_uploader.OSS_CONFIG_FILE.write_text(json.dumps(data))

    def test_load_valid_config(self):
        self._write_config({
            "endpoint": "https://oss.example.com",
            "bucket": "test-bucket",
            "access_key_id": "key123",
            "access_key_secret": "secret123",
        })
        config = oss_uploader.load_oss_config()
        self.assertEqual(config["endpoint"], "https://oss.example.com")
        self.assertEqual(config["bucket"], "test-bucket")

    def test_load_missing_config(self):
        config = oss_uploader.load_oss_config()
        self.assertEqual(config, {})

    def test_load_config_public_url_present(self):
        self._write_config({
            "endpoint": "https://oss.example.com",
            "bucket": "test-bucket",
            "access_key_id": "key123",
            "access_key_secret": "secret123",
            "public_url": "https://test-bucket.oss.example.com",
        })
        config = oss_uploader.load_oss_config()
        self.assertEqual(config["public_url"], "https://test-bucket.oss.example.com")

    def test_load_config_auto_public_url(self):
        self._write_config({
            "endpoint": "https://oss-ap-southeast-7.aliyuncs.com",
            "bucket": "test-bucket",
            "access_key_id": "key123",
            "access_key_secret": "secret123",
        })
        config = oss_uploader.load_oss_config()
        self.assertIn("public_url", config)
        self.assertIn("test-bucket", config["public_url"])


class TestOssUrl(unittest.TestCase):
    def test_get_oss_url(self):
        config = {"public_url": "https://test-bucket.oss.example.com"}
        url = oss_uploader.get_oss_url(config, "channel_id/photo/test.jpg")
        self.assertEqual(
            url,
            "https://test-bucket.oss.example.com/channel_id/photo/test.jpg"
        )

    def test_get_oss_url_strips_leading_slash(self):
        config = {"public_url": "https://test-bucket.oss.example.com"}
        url = oss_uploader.get_oss_url(config, "/channel_id/photo/test.jpg")
        self.assertEqual(
            url,
            "https://test-bucket.oss.example.com/channel_id/photo/test.jpg"
        )

    def test_get_oss_url_url_encode_spaces(self):
        config = {"public_url": "https://test-bucket.oss.example.com"}
        url = oss_uploader.get_oss_url(config, "ch/photo/file name.jpg")
        self.assertIn("file%20name.jpg", url)


class TestUploadFile(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.test_file = Path(self.tmpdir.name) / "test.jpg"
        self.test_file.write_text("fake-image-data")

    def tearDown(self):
        self.tmpdir.cleanup()

    @patch("oss_uploader.oss2")
    def test_upload_media_photo(self, mock_oss2):
        mock_bucket = MagicMock()
        mock_oss2.Bucket.return_value = mock_bucket

        config = {
            "endpoint": "https://oss.example.com",
            "bucket": "test-bucket",
            "access_key_id": "key",
            "access_key_secret": "secret",
            "public_url": "https://test-bucket.oss.example.com",
        }
        url = oss_uploader.upload_media(
            config, str(self.test_file), "test_ch", "test_photo.jpg", "photo"
        )
        expected_key = "test_ch/photo/test_photo.jpg"
        mock_bucket.put_object_from_file.assert_called_once()
        call_args = mock_bucket.put_object_from_file.call_args[0]
        self.assertEqual(call_args[0], expected_key)
        self.assertTrue(url.startswith("https://test-bucket.oss.example.com/"))
        self.assertIn(expected_key, url)

    @patch("oss_uploader.oss2")
    def test_upload_media_video(self, mock_oss2):
        mock_bucket = MagicMock()
        mock_oss2.Bucket.return_value = mock_bucket

        config = {
            "endpoint": "https://oss.example.com",
            "bucket": "test-bucket",
            "access_key_id": "key",
            "access_key_secret": "secret",
            "public_url": "https://test-bucket.oss.example.com",
        }
        url = oss_uploader.upload_media(
            config, str(self.test_file), "test_ch", "test_video.mp4", "video"
        )
        expected_key = "test_ch/video/test_video.mp4"
        call_args = mock_bucket.put_object_from_file.call_args[0]
        self.assertEqual(call_args[0], expected_key)


class TestUploadFileIntegration(unittest.TestCase):
    """Integration tests with real OSS (requires valid credentials)."""
    def setUp(self):
        self.config = oss_uploader.load_oss_config()
        self.tmpdir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_real_upload_and_delete(self):
        if not self.config:
            self.skipTest("No OSS config available")

        test_path = Path(self.tmpdir.name) / "oss_test.txt"
        test_path.write_text("oss-integration-test-content")

        url = oss_uploader.upload_media(
            self.config, str(test_path), "_test", "oss_test.txt", "photo"
        )
        self.assertTrue(url.startswith("https://"))
        self.assertIn("_test/photo/oss_test.txt", url)

    def test_oss_public_url(self):
        if not self.config:
            self.skipTest("No OSS config available")
        self.assertIn("public_url", self.config)
        self.assertTrue(self.config["public_url"].startswith("https://"))


if __name__ == "__main__":
    unittest.main()
