"""
Tests for media classification logic.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tg_core import classify_media


class TestClassifyMedia(unittest.TestCase):
    def test_photo_returns_photo(self):
        media_type, mime_type = classify_media(is_photo=True, is_document=False)
        self.assertEqual(media_type, "photo")
        self.assertIsNone(mime_type)

    def test_video_document_returns_document_with_mime(self):
        media_type, mime_type = classify_media(
            is_photo=False, is_document=True, mime_type="video/mp4"
        )
        self.assertEqual(media_type, "document")
        self.assertEqual(mime_type, "video/mp4")

    def test_image_document_returns_document_with_mime(self):
        media_type, mime_type = classify_media(
            is_photo=False, is_document=True, mime_type="image/jpeg"
        )
        self.assertEqual(media_type, "document")
        self.assertEqual(mime_type, "image/jpeg")

    def test_document_empty_mime_defaults_to_empty_string(self):
        media_type, mime_type = classify_media(
            is_photo=False, is_document=True, mime_type=""
        )
        self.assertEqual(media_type, "document")
        self.assertEqual(mime_type, "")

    def test_neither_photo_nor_document_returns_unknown(self):
        media_type, mime_type = classify_media(
            is_photo=False, is_document=False
        )
        self.assertEqual(media_type, "unknown")
        self.assertIsNone(mime_type)

    def test_default_mime_type_is_empty_string(self):
        media_type, mime_type = classify_media(
            is_photo=False, is_document=True
        )
        self.assertEqual(media_type, "document")
        self.assertEqual(mime_type, "")

    def test_both_photo_and_document_raises_error(self):
        with self.assertRaises(ValueError) as ctx:
            classify_media(is_photo=True, is_document=True)
        self.assertIn("both", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
