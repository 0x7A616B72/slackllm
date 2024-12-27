import unittest
from unittest.mock import Mock, patch
from handlers.message_handler import MessageHandler

class TestMessageHandler(unittest.TestCase):
    @patch('handlers.message_handler.BedrockService')
    @patch('handlers.message_handler.MessagePreparationHelper')
    @patch('handlers.message_handler.UserPreferencesAccessor') 
    def setUp(self, mock_prefs, mock_message_prep, mock_bedrock):
        self.handler = MessageHandler()
        self.mock_say = Mock()
        self.mock_app_client = Mock()
        self.mock_app_client.auth_test.return_value = {"user_id": "BOT123"}
        self.mock_app_client.token = "xoxb-test-token"
        
        # Setup mocked dependencies
        self.mock_bedrock = mock_bedrock
        self.mock_bedrock_instance = mock_bedrock.return_value
        self.mock_message_prep = mock_message_prep
        self.mock_message_prep_instance = mock_message_prep.return_value
        self.mock_prefs = mock_prefs
        self.mock_prefs_instance = mock_prefs.return_value
        self.mock_prefs_instance.get_user_model.return_value = "model123"

    def test_handle_mention(self):
        # Setup
        self.mock_bedrock_instance.invoke_model.return_value = "Bot response"
        self.mock_message_prep_instance.prepare_message.return_value = {
            "role": "user",
            "content": [{"text": "Hello bot"}]
        }

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
        self.mock_message_prep_instance.prepare_message.assert_called_once_with(
            "Hello bot",
            [],
            self.mock_app_client
        )
        self.mock_bedrock_instance.invoke_model.assert_called_once_with([{
            "role": "user",
            "content": [{"text": "Hello bot"}]
        }], "model123")
        self.mock_say.assert_called_once_with("Bot response", thread_ts="123.456")

    def test_handle_direct_message(self):
        # Setup
        self.mock_bedrock_instance.invoke_model.return_value = "Bot response"
        self.mock_message_prep_instance.prepare_message.return_value = {
            "role": "user",
            "content": [{"text": "Hello bot"}]
        }

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
        self.mock_message_prep_instance.prepare_message.assert_called_once_with(
            "Hello bot",
            [],
            self.mock_app_client
        )
        self.mock_bedrock_instance.invoke_model.assert_called_once_with([{
            "role": "user",
            "content": [{"text": "Hello bot"}]
        }], "model123")
        self.mock_say.assert_called_once_with("Bot response", thread_ts="123.456")

    def test_handle_thread_with_files(self):
        # Setup
        self.mock_bedrock_instance.invoke_model.return_value = "Bot response"
        
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

        # Mock the message preparation for each message in the thread
        self.mock_message_prep_instance.prepare_message.side_effect = [
            {"role": "user", "content": [{"text": "Check these files"}, {"type": "file", "content": "file1_content"}]},
            {"role": "user", "content": [{"text": "And this one too"}, {"type": "file", "content": "file2_content"}]},
            {"role": "user", "content": [{"text": "Thanks!"}]}
        ]

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
        # Verify that message preparation was called for each user message
        self.assertEqual(self.mock_message_prep_instance.prepare_message.call_count, 3)
        self.mock_say.assert_called_once_with("Bot response", thread_ts="123.000")

if __name__ == '__main__':
    unittest.main()