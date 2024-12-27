import unittest
from unittest.mock import Mock, patch
from service.message_preparation_helper import MessagePreparationHelper

class TestMessagePreparationHelper(unittest.TestCase):
    @patch('service.message_preparation_helper.FileService')
    def setUp(self, mock_file_service):
        self.helper = MessagePreparationHelper()
        self.mock_app_client = Mock()
        self.mock_app_client.token = "xoxb-test-token"
        
        # Setup mocked dependencies
        self.mock_file_service = mock_file_service
        self.mock_file_service_instance = mock_file_service.return_value

    def test_prepare_message_no_files(self):
        # Test preparing a message with no files
        result = self.helper.prepare_message("Hello", [], self.mock_app_client)
        expected = {
            "role": "user",
            "content": [{"text": "Hello"}]
        }
        self.assertEqual(result, expected)

    def test_prepare_message_with_image(self):
        # Setup
        self.mock_file_service_instance.download_file.return_value = b"image_content"

        test_file = {
            "name": "test.png",
            "filetype": "png",
            "url_private_download": "https://files.slack.com/test.png"
        }

        # Execute
        result = self.helper.prepare_message("Check this image", [test_file], self.mock_app_client)

        # Assert
        self.mock_file_service_instance.download_file.assert_called_once_with(
            "https://files.slack.com/test.png",
            {"Authorization": "Bearer xoxb-test-token"}
        )

        expected = {
            "role": "user",
            "content": [
                {"text": "Check this image"},
                {
                    "image": {
                        "format": "png",
                        "source": {
                            "bytes": b"image_content"
                        }
                    }
                }
            ]
        }
        self.assertEqual(result, expected)

    def test_prepare_message_with_document(self):
        # Setup
        self.mock_file_service_instance.download_file.return_value = b"document_content"

        test_file = {
            "name": "test.txt",
            "filetype": "txt",
            "url_private_download": "https://files.slack.com/test.txt"
        }

        # Execute
        result = self.helper.prepare_message("Check this document", [test_file], self.mock_app_client)

        # Assert
        self.mock_file_service_instance.download_file.assert_called_once_with(
            "https://files.slack.com/test.txt",
            {"Authorization": "Bearer xoxb-test-token"}
        )

        expected = {
            "role": "user",
            "content": [
                {"text": "Check this document"},
                {
                    "document": {
                        "name": "test_txt",
                        "format": "txt",
                        "source": {
                            "bytes": b"document_content"
                        }
                    }
                }
            ]
        }
        self.assertEqual(result, expected)

    def test_prepare_message_with_video(self):
        # Setup
        self.mock_file_service_instance.download_file.return_value = b"video_content"

        test_file = {
            "name": "test.mp4",
            "filetype": "mp4",
            "url_private_download": "https://files.slack.com/test.mp4"
        }

        # Execute
        result = self.helper.prepare_message("Check this video", [test_file], self.mock_app_client)

        # Assert
        self.mock_file_service_instance.download_file.assert_called_once_with(
            "https://files.slack.com/test.mp4",
            {"Authorization": "Bearer xoxb-test-token"}
        )

        expected = {
            "role": "user",
            "content": [
                {"text": "Check this video"},
                {
                    "video": {
                        "format": "mp4",
                        "source": {
                            "bytes": b"video_content"
                        }
                    }
                }
            ]
        }
        self.assertEqual(result, expected)

    def test_prepare_message_with_file_error(self):
        # Setup
        self.mock_file_service_instance.download_file.side_effect = Exception("Download failed")

        test_file = {
            "name": "test.txt",
            "filetype": "txt",
            "url_private_download": "https://files.slack.com/test.txt"
        }

        # Execute
        result = self.helper.prepare_message("Check this file", [test_file], self.mock_app_client)

        # Assert
        expected = {
            "role": "user",
            "content": [{"text": "Check this file (Note: Failed to process attached file: test.txt)"}]
        }
        self.assertEqual(result, expected)

    def test_prepare_message_with_unsupported_file_type(self):
        # Setup
        self.mock_file_service_instance.download_file.return_value = b"file_content"

        test_file = {
            "name": "test.xyz",
            "filetype": "xyz",
            "url_private_download": "https://files.slack.com/test.xyz"
        }

        # Execute and Assert
        with self.assertRaises(ValueError) as context:
            self.helper.prepare_message("Check this file", [test_file], self.mock_app_client)

        expected_error = (
            "Unsupported file type: xyz. Supported types are: "
            f"images ({', '.join(self.helper.SUPPORTED_IMAGE_TYPES)}), "
            f"videos ({', '.join(self.helper.SUPPORTED_VIDEO_TYPES)}), and "
            f"documents ({', '.join(self.helper.SUPPORTED_DOCUMENT_TYPES)})"
        )
        self.assertEqual(str(context.exception), expected_error)

    def test_prepare_message_with_jpg_image(self):
        # Setup
        self.mock_file_service_instance.download_file.return_value = b"image_content"

        test_file = {
            "name": "test.jpg",
            "filetype": "jpg",
            "url_private_download": "https://files.slack.com/test.jpg"
        }

        # Execute
        result = self.helper.prepare_message("Check this image", [test_file], self.mock_app_client)

        # Assert
        expected = {
            "role": "user",
            "content": [
                {"text": "Check this image"},
                {
                    "image": {
                        "format": "jpeg",  # jpg should be converted to jpeg
                        "source": {
                            "bytes": b"image_content"
                        }
                    }
                }
            ]
        }
        self.assertEqual(result, expected)

    def test_prepare_message_with_uppercase_filetype(self):
        # Setup
        self.mock_file_service_instance.download_file.return_value = b"image_content"

        test_file = {
            "name": "test.PNG",
            "filetype": "PNG",
            "url_private_download": "https://files.slack.com/test.PNG"
        }

        # Execute
        result = self.helper.prepare_message("Check this image", [test_file], self.mock_app_client)

        # Assert
        expected = {
            "role": "user",
            "content": [
                {"text": "Check this image"},
                {
                    "image": {
                        "format": "png",
                        "source": {
                            "bytes": b"image_content"
                        }
                    }
                }
            ]
        }
        self.assertEqual(result, expected) 