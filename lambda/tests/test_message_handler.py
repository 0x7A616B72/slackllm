import unittest
from unittest.mock import Mock, patch
from handlers.message_handler import MessageHandler

class TestMessageHandler(unittest.TestCase):
    @patch('handlers.message_handler.BedrockService')
    @patch('handlers.message_handler.FileService')
    @patch('handlers.message_handler.UserPreferencesAccessor') 
    def setUp(self, mock_prefs, mock_file_service, mock_bedrock):
        self.handler = MessageHandler()
        self.mock_say = Mock()
        self.mock_app_client = Mock()
        self.mock_app_client.auth_test.return_value = {"user_id": "BOT123"}
        self.mock_app_client.token = "xoxb-test-token"
        
        # Setup mocked dependencies
        self.mock_bedrock = mock_bedrock
        self.mock_bedrock_instance = mock_bedrock.return_value
        self.mock_file_service = mock_file_service
        self.mock_file_service_instance = mock_file_service.return_value
        self.mock_prefs = mock_prefs
        self.mock_prefs_instance = mock_prefs.return_value
        self.mock_prefs_instance.get_user_model.return_value = "model123"

    def test_handle_mention(self):
        # Setup
        self.mock_bedrock_instance.invoke_model.return_value = "Bot response"

        body = {
            "event": {
                "text": "<@BOT123> Hello bot",
                "user": "USER123",
                "ts": "123.456",
                "files": []
            }
        }

        # Execute
        self.handler.handle_message(body, self.mock_say, self.mock_app_client)

        # Assert
        expected_message = {
            "role": "user",
            "content": [{"text": "Hello bot"}]
        }
        self.mock_bedrock_instance.invoke_model.assert_called_once_with([expected_message], "model123")
        self.mock_say.assert_called_once_with("Bot response", thread_ts="123.456")

    def test_handle_mention_with_image(self):
        # Setup
        self.mock_bedrock_instance.invoke_model.return_value = "Bot response"
        self.mock_file_service_instance.download_file.return_value = b"image_content"

        test_file = {
            "name": "test.png",
            "filetype": "png",
            "url_private_download": "https://files.slack.com/test.png"
        }

        body = {
            "event": {
                "text": "<@BOT123> What's in this image?",
                "user": "USER123",
                "ts": "123.456",
                "files": [test_file]
            }
        }

        # Execute
        self.handler.handle_message(body, self.mock_say, self.mock_app_client)

        # Assert
        self.mock_file_service_instance.download_file.assert_called_once_with(
            "https://files.slack.com/test.png",
            {"Authorization": "Bearer xoxb-test-token"}
        )

        expected_message = {
            "role": "user",
            "content": [
                {"text": "What's in this image?"},
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
        self.mock_bedrock_instance.invoke_model.assert_called_once_with([expected_message], "model123")
        self.mock_say.assert_called_once_with("Bot response", thread_ts="123.456")

    def test_handle_mention_with_document(self):
        # Setup
        self.mock_bedrock_instance.invoke_model.return_value = "Bot response"
        self.mock_file_service_instance.download_file.return_value = b"document_content"

        test_file = {
            "name": "test.txt",
            "filetype": "txt",
            "url_private_download": "https://files.slack.com/test.txt"
        }

        body = {
            "event": {
                "text": "<@BOT123> What's in this document?",
                "user": "USER123",
                "ts": "123.456",
                "files": [test_file]
            }
        }

        # Execute
        self.handler.handle_message(body, self.mock_say, self.mock_app_client)

        # Assert
        self.mock_file_service_instance.download_file.assert_called_once_with(
            "https://files.slack.com/test.txt",
            {"Authorization": "Bearer xoxb-test-token"}
        )

        expected_message = {
            "role": "user",
            "content": [
                {"text": "What's in this document?"},
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
        self.mock_bedrock_instance.invoke_model.assert_called_once_with([expected_message], "model123")
        self.mock_say.assert_called_once_with("Bot response", thread_ts="123.456")

    def test_handle_mention_with_video(self):
        # Setup
        self.mock_bedrock_instance.invoke_model.return_value = "Bot response"
        self.mock_file_service_instance.download_file.return_value = b"video_content"

        test_file = {
            "name": "test.mp4",
            "filetype": "mp4",
            "url_private_download": "https://files.slack.com/test.mp4"
        }

        body = {
            "event": {
                "text": "<@BOT123> What's in this video?",
                "user": "USER123",
                "ts": "123.456",
                "files": [test_file]
            }
        }

        # Execute
        self.handler.handle_message(body, self.mock_say, self.mock_app_client)

        # Assert
        self.mock_file_service_instance.download_file.assert_called_once_with(
            "https://files.slack.com/test.mp4",
            {"Authorization": "Bearer xoxb-test-token"}
        )

        expected_message = {
            "role": "user",
            "content": [
                {"text": "What's in this video?"},
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
        self.mock_bedrock_instance.invoke_model.assert_called_once_with([expected_message], "model123")
        self.mock_say.assert_called_once_with("Bot response", thread_ts="123.456")

    def test_handle_mention_with_file_error(self):
        # Setup
        self.mock_bedrock_instance.invoke_model.return_value = "Bot response"
        self.mock_file_service_instance.download_file.side_effect = Exception("Download failed")

        test_file = {
            "name": "test.txt",
            "filetype": "txt",
            "url_private_download": "https://files.slack.com/test.txt"
        }

        body = {
            "event": {
                "text": "<@BOT123> Check this file",
                "user": "USER123",
                "ts": "123.456",
                "files": [test_file]
            }
        }

        # Execute
        self.handler.handle_message(body, self.mock_say, self.mock_app_client)

        # Assert
        expected_message = {
            "role": "user",
            "content": [{"text": "Check this file (Note: Failed to process attached file: test.txt)"}]
        }
        self.mock_bedrock_instance.invoke_model.assert_called_once_with([expected_message], "model123")
        self.mock_say.assert_called_once_with("Bot response", thread_ts="123.456")

    def test_handle_direct_message(self):
        # Setup
        self.mock_bedrock_instance.invoke_model.return_value = "Bot response"

        body = {
            "event": {
                "text": "Hello bot",
                "user": "USER123",
                "ts": "123.456",
                "channel_type": "im",
                "files": []
            }
        }

        # Execute
        self.handler.handle_message(body, self.mock_say, self.mock_app_client)

        # Assert
        expected_message = {"role": "user", "content": [{"text": "Hello bot"}]}
        self.mock_bedrock_instance.invoke_model.assert_called_once_with([expected_message], "model123")
        self.mock_say.assert_called_once_with("Bot response", thread_ts="123.456")

    def test_handle_thread_with_files(self):
        # Setup
        self.mock_bedrock_instance.invoke_model.return_value = "Bot response"
        self.mock_file_service_instance.download_file.return_value = b"file_content"

        test_file1 = {
            "name": "test1.txt",
            "filetype": "txt",
            "url_private_download": "https://files.slack.com/test1.txt"
        }
        test_file2 = {
            "name": "test2.txt",
            "filetype": "txt",
            "url_private_download": "https://files.slack.com/test2.txt"
        }

        self.mock_app_client.conversations_replies.return_value = {
            "messages": [
                {"user": "USER123", "text": "Check these files", "files": [test_file1]},
                {"user": "USER123", "text": "And this one too", "files": [test_file2]},
                {"user": "BOT123", "text": "Looking at them", "files": []},
                {"user": "USER123", "text": "Thanks!", "files": []}
            ]
        }

        body = {
            "event": {
                "text": "Thanks!",
                "user": "USER123",
                "ts": "123.456",
                "thread_ts": "123.000",
                "channel": "C123",
                "files": []
            }
        }

        # Execute
        self.handler.handle_message(body, self.mock_say, self.mock_app_client)

        # Assert
        # Verify that files from consecutive messages were combined
        self.assertEqual(self.mock_file_service_instance.download_file.call_count, 2)
        self.mock_file_service_instance.download_file.assert_any_call(
            "https://files.slack.com/test1.txt",
            {"Authorization": "Bearer xoxb-test-token"}
        )
        self.mock_file_service_instance.download_file.assert_any_call(
            "https://files.slack.com/test2.txt",
            {"Authorization": "Bearer xoxb-test-token"}
        )
        self.mock_say.assert_called_once_with("Bot response", thread_ts="123.000")

    def test_prepare_message_with_file_image(self):
        # Setup
        file_content = b"image_content"
        file_info = {
            "name": "test.png",
            "filetype": "png"
        }
        text = "Check this image"

        # Execute
        result = self.handler._prepare_message_with_file(text, file_content, file_info)

        # Assert
        expected_message = {
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
        self.assertEqual(result, expected_message)

    def test_prepare_message_with_file_image_uppercase(self):
        # Setup
        file_content = b"image_content"
        file_info = {
            "name": "test.PNG",
            "filetype": "PNG"
        }
        text = "Check this image"

        # Execute
        result = self.handler._prepare_message_with_file(text, file_content, file_info)

        # Assert
        expected_message = {
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
        self.assertEqual(result, expected_message)

    def test_prepare_message_with_file_document(self):
        # Test each supported document type
        supported_types = ["pdf", "csv", "doc", "docx", "xls", "xlsx", "html", "txt", "md"]
        
        for doc_type in supported_types:
            with self.subTest(doc_type=doc_type):
                # Setup
                file_content = b"document_content"
                file_info = {
                    "name": f"test.{doc_type}",
                    "filetype": doc_type
                }
                text = f"Check this {doc_type} document"

                # Execute
                result = self.handler._prepare_message_with_file(text, file_content, file_info)

                # Assert
                expected_message = {
                    "role": "user",
                    "content": [
                        {"text": f"Check this {doc_type} document"},
                        {
                            "document": {
                                "name": f"test_{doc_type}",
                                "format": doc_type,
                                "source": {
                                    "bytes": b"document_content"
                                }
                            }
                        }
                    ]
                }
                self.assertEqual(result, expected_message)

    def test_prepare_message_with_unsupported_file_type(self):
        # Setup
        file_content = b"file_content"
        file_info = {
            "name": "test.xyz",
            "filetype": "xyz"
        }
        text = "Check this file"

        # Execute and Assert
        with self.assertRaises(ValueError) as context:
            self.handler._prepare_message_with_file(text, file_content, file_info)

        # Verify error message
        error_msg = str(context.exception)
        self.assertIn("Unsupported file type: xyz", error_msg)
        self.assertIn("images (png, jpg, jpeg, gif, webp)", error_msg)
        self.assertIn("documents (pdf, csv, doc, docx, xls, xlsx, html, txt, md)", error_msg)

    def test_prepare_message_with_file_document_uppercase(self):
        # Setup
        file_content = b"document_content"
        file_info = {
            "name": "test.PDF",
            "filetype": "PDF"
        }
        text = "Check this PDF document"

        # Execute
        result = self.handler._prepare_message_with_file(text, file_content, file_info)

        # Assert
        expected_message = {
            "role": "user",
            "content": [
                {"text": "Check this PDF document"},
                {
                    "document": {
                        "name": "test_PDF",
                        "format": "pdf",
                        "source": {
                            "bytes": b"document_content"
                        }
                    }
                }
            ]
        }
        self.assertEqual(result, expected_message)

    def test_prepare_message_with_file_video(self):
        # Test each supported video type
        supported_types = ["mov", "mkv", "mp4", "webm", "flv", "mpeg", "mpg", "wmv", "three_gp"]
        
        for video_type in supported_types:
            with self.subTest(video_type=video_type):
                # Setup
                file_content = b"video_content"
                file_info = {
                    "name": f"test.{video_type}",
                    "filetype": video_type
                }
                text = f"Check this {video_type} video"

                # Execute
                result = self.handler._prepare_message_with_file(text, file_content, file_info)

                # Assert
                expected_message = {
                    "role": "user",
                    "content": [
                        {"text": f"Check this {video_type} video"},
                        {
                            "video": {
                                "format": video_type,
                                "source": {
                                    "bytes": b"video_content"
                                }
                            }
                        }
                    ]
                }
                self.assertEqual(result, expected_message)

    def test_prepare_message_with_file_video_uppercase(self):
        # Setup
        file_content = b"video_content"
        file_info = {
            "name": "test.MP4",
            "filetype": "MP4"
        }
        text = "Check this MP4 video"

        # Execute
        result = self.handler._prepare_message_with_file(text, file_content, file_info)

        # Assert
        expected_message = {
            "role": "user",
            "content": [
                {"text": "Check this MP4 video"},
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
        self.assertEqual(result, expected_message)

if __name__ == '__main__':
    unittest.main() 