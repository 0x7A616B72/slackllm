import unittest
from unittest.mock import Mock, patch
from handlers.message_handler import MessageHandler

class TestMessageHandler(unittest.TestCase):
    @patch('handlers.message_handler.BedrockService')
    @patch('handlers.message_handler.UserPreferencesAccessor') 
    def setUp(self, mock_prefs, mock_bedrock):
        self.handler = MessageHandler()
        self.mock_say = Mock()
        self.mock_app_client = Mock()
        self.mock_app_client.auth_test.return_value = {"user_id": "BOT123"}
        
        # Setup mocked dependencies
        self.mock_bedrock = mock_bedrock
        self.mock_bedrock_instance = mock_bedrock.return_value
        self.mock_prefs = mock_prefs
        self.mock_prefs_instance = mock_prefs.return_value

    def test_handle_mention(self):
        # Setup
        self.mock_bedrock_instance.invoke_model.return_value = "Bot response"
        self.mock_prefs_instance.get_user_model.return_value = "model123"

        body = {
            "event": {
                "text": "<@BOT123> Hello bot",
                "user": "USER123",
                "ts": "123.456"
            }
        }

        # Execute
        self.handler.handle_message(body, self.mock_say, self.mock_app_client)

        # Assert
        expected_message = [{"role": "user", "content": [{"text": "Hello bot"}]}]
        self.mock_bedrock_instance.invoke_model.assert_called_once_with(expected_message, "model123")
        self.mock_say.assert_called_once_with("Bot response", thread_ts="123.456")

    def test_handle_direct_message(self):
        # Setup
        self.mock_bedrock_instance.invoke_model.return_value = "Bot response"

        body = {
            "event": {
                "text": "Hello bot",
                "user": "USER123",
                "ts": "123.456",
                "channel_type": "im"
            }
        }

        # Execute
        self.handler.handle_message(body, self.mock_say, self.mock_app_client)

        # Assert
        expected_message = [{"role": "user", "content": [{"text": "Hello bot"}]}]
        self.mock_bedrock_instance.invoke_model.assert_called_once()
        self.mock_say.assert_called_once_with("Bot response", thread_ts="123.456")

    def test_handle_thread(self):
        # Setup
        self.mock_bedrock_instance.invoke_model.return_value = "Bot response"
        self.mock_app_client.conversations_replies.return_value = {
            "messages": [
                {"user": "USER123", "text": "Hello"},
                {"user": "BOT123", "text": "Hi"},
                {"user": "USER123", "text": "How are you?"}
            ]
        }

        body = {
            "event": {
                "text": "How are you?",
                "user": "USER123",
                "ts": "123.456",
                "thread_ts": "123.000",
                "channel": "C123"
            }
        }

        # Execute
        self.handler.handle_message(body, self.mock_say, self.mock_app_client)

        # Assert
        self.mock_app_client.conversations_replies.assert_called_once_with(
            channel="C123",
            ts="123.000",
            limit=100
        )
        self.mock_bedrock_instance.invoke_model.assert_called_once()
        self.mock_say.assert_called_once_with("Bot response", thread_ts="123.000")

    def test_handle_thread_no_bot_response(self):
        # Setup
        self.mock_app_client.conversations_replies.return_value = {
            "messages": [
                {"user": "USER123", "text": "Hello"},
                {"user": "USER456", "text": "Hi"},
            ]
        }

        body = {
            "event": {
                "text": "How are you?",
                "user": "USER123",
                "ts": "123.456",
                "thread_ts": "123.000",
                "channel": "C123"
            }
        }

        # Execute
        self.handler.handle_message(body, self.mock_say, self.mock_app_client)

        # Assert
        self.mock_bedrock_instance.invoke_model.assert_not_called()
        self.mock_say.assert_not_called()

    def test_handle_error_in_mention(self):
        # Setup
        self.mock_bedrock_instance.invoke_model.side_effect = Exception("Test error")

        body = {
            "event": {
                "text": "<@BOT123> Hello bot",
                "user": "USER123",
                "ts": "123.456"
            }
        }

        # Execute
        self.handler.handle_message(body, self.mock_say, self.mock_app_client)

        # Assert
        self.mock_say.assert_called_once_with(text="Error: Test error", thread_ts="123.456")

if __name__ == '__main__':
    unittest.main() 