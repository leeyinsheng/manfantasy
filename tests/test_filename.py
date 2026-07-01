"""
Tests for filename generation and MIME utility functions.
"""
import sys
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tg_core import (
    generate_photo_filename,
    generate_document_filename,
    get_original_filename,
    mime_to_extension,
    is_video_mime,
    append_id_to_filename,
)


class TestPhotoFilename(unittest.TestCase):
    def test_generates_correct_format(self):
        date = datetime(2025, 2, 1, 14, 30, 22)
        result = generate_photo_filename(date, 1234)
        self.assertEqual(result, "20250201_143022_photo_1234.jpg")

    def test_single_digit_month_and_day(self):
        date = datetime(2025, 1, 5, 8, 5, 3)
        result = generate_photo_filename(date, 99)
        self.assertEqual(result, "20250105_080503_photo_99.jpg")


class TestDocumentFilename(unittest.TestCase):
    def test_uses_original_name_when_present(self):
        date = datetime(2025, 2, 1, 14, 30, 22)
        result = generate_document_filename(date, 1234, "my_video.mp4", "video/mp4")
        self.assertEqual(result, "my_video.mp4")

    def test_strips_whitespace_from_original_name(self):
        date = datetime(2025, 2, 1, 14, 30, 22)
        result = generate_document_filename(date, 1234, "  file name.mp4  ", "video/mp4")
        self.assertEqual(result, "file name.mp4")

    def test_fallback_for_video_without_name(self):
        date = datetime(2025, 2, 1, 14, 30, 22)
        result = generate_document_filename(date, 1234, "", "video/mp4")
        self.assertEqual(result, "20250201_143022_media_1234.mp4")

    def test_fallback_for_image_without_name(self):
        date = datetime(2025, 2, 1, 14, 30, 22)
        result = generate_document_filename(date, 1234, "", "image/jpeg")
        self.assertEqual(result, "20250201_143022_media_1234.jpg")

    def test_fallback_for_unknown_mime_without_name(self):
        date = datetime(2025, 2, 1, 14, 30, 22)
        result = generate_document_filename(date, 1234, "", "application/pdf")
        self.assertEqual(result, "20250201_143022_media_1234.bin")


class TestGetOriginalFilename(unittest.TestCase):
    class FakeAttr:
        def __init__(self):
            self.file_name = None

    def test_returns_filename_from_attr(self):
        attr = self.FakeAttr()
        attr.file_name = "video.mp4"
        result = get_original_filename([attr])
        self.assertEqual(result, "video.mp4")

    def test_returns_first_filename_only(self):
        attr1 = self.FakeAttr()
        attr1.file_name = "first.mp4"
        attr2 = self.FakeAttr()
        attr2.file_name = "second.mp4"
        result = get_original_filename([attr1, attr2])
        self.assertEqual(result, "first.mp4")

    def test_returns_empty_when_no_file_name_attr(self):
        attr = self.FakeAttr()
        result = get_original_filename([attr])
        self.assertEqual(result, "")

    def test_returns_empty_for_empty_list(self):
        result = get_original_filename([])
        self.assertEqual(result, "")


class TestMimeToExtension(unittest.TestCase):
    def test_video_mime_returns_mp4(self):
        self.assertEqual(mime_to_extension("video/mp4"), ".mp4")
        self.assertEqual(mime_to_extension("video/quicktime"), ".mp4")
        self.assertEqual(mime_to_extension("video/webm"), ".mp4")

    def test_image_mime_returns_jpg(self):
        self.assertEqual(mime_to_extension("image/jpeg"), ".jpg")
        self.assertEqual(mime_to_extension("image/png"), ".jpg")
        self.assertEqual(mime_to_extension("image/gif"), ".jpg")

    def test_unknown_mime_returns_bin(self):
        self.assertEqual(mime_to_extension("application/pdf"), ".bin")
        self.assertEqual(mime_to_extension("audio/mp3"), ".bin")
        self.assertEqual(mime_to_extension(""), ".bin")


class TestIsVideoMime(unittest.TestCase):
    def test_video_mime_returns_true(self):
        self.assertTrue(is_video_mime("video/mp4"))
        self.assertTrue(is_video_mime("video/quicktime"))

    def test_non_video_mime_returns_false(self):
        self.assertFalse(is_video_mime("image/jpeg"))
        self.assertFalse(is_video_mime("application/pdf"))
        self.assertFalse(is_video_mime(""))


class TestAppendIdToFilename(unittest.TestCase):
    def test_appends_id_to_stem(self):
        result = append_id_to_filename("my_video.mp4", 9999)
        self.assertEqual(result, "my_video_9999.mp4")

    def test_handles_multiple_dots(self):
        result = append_id_to_filename("archive.tar.gz", 42)
        self.assertEqual(result, "archive.tar_42.gz")

    def test_handles_no_extension(self):
        result = append_id_to_filename("README", 5)
        self.assertEqual(result, "README_5")


if __name__ == "__main__":
    unittest.main()
