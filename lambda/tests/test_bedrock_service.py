import unittest
from unittest.mock import Mock, patch
from botocore.exceptions import ClientError
from service.bedrock_service import BedrockService

TEST_MODEL_ID = "test.model.id"
ALTERNATE_MODEL_ID = "alternate.model.id"

class TestBedrockService(unittest.TestCase):
    @patch('boto3.client')
    def setUp(self, mock_boto3_client):
        self.mock_client = Mock()
        mock_boto3_client.return_value = self.mock_client
        self.service = BedrockService()
        self.test_messages = [
            {
                "role": "user", 
                "content": [{"text": "Hello"}]
            }
        ]
        self.mock_response = {
            "output": {
                "message": {
                    "content": [{"text": "Hello there!"}]
                }
            },
            "usage": {
                "inputTokens": 10,
                "outputTokens": 20,
                "totalTokens": 30
            },
            "stopReason": "complete"
        }

    @patch('service.bedrock_service.DEFAULT_BEDROCK_MODEL_ID', TEST_MODEL_ID)
    def test_should_invoke_model_with_default_model_successfully(self):
        # Setup
        self.mock_client.converse = Mock(return_value=self.mock_response)

        # Execute
        result = self.service.invoke_model(self.test_messages)

        # Assert
        self.assertEqual(result, "Hello there!")
        
        # Get the actual call arguments
        call_args = self.mock_client.converse.call_args
        
        # Assert the messages and modelId match exactly
        self.assertEqual(call_args.kwargs['messages'], self.test_messages)
        self.assertEqual(call_args.kwargs['modelId'], TEST_MODEL_ID)
        
        # Assert the system prompt is present
        self.assertIn('system', call_args.kwargs)
        self.assertTrue(len(call_args.kwargs['system']) == 1)
        self.assertIn('text', call_args.kwargs['system'][0])

    @patch('service.bedrock_service.DEFAULT_BEDROCK_MODEL_ID', TEST_MODEL_ID)
    def test_should_invoke_model_with_custom_model_successfully(self):
        # Setup
        self.mock_client.converse = Mock(return_value={
            "output": {
                "message": {
                    "content": [{"text": "Custom model response"}]
                }
            },
            "usage": {
                "inputTokens": 10,
                "outputTokens": 20,
                "totalTokens": 30
            },
            "stopReason": "complete"
        })

        # Execute
        result = self.service.invoke_model(self.test_messages, ALTERNATE_MODEL_ID)

        # Assert
        self.assertEqual(result, "Custom model response")
        
        # Get the actual call arguments
        call_args = self.mock_client.converse.call_args
        
        # Assert the messages and modelId match exactly
        self.assertEqual(call_args.kwargs['messages'], self.test_messages)
        self.assertEqual(call_args.kwargs['modelId'], ALTERNATE_MODEL_ID)
        
        # Assert the system prompt is present
        self.assertIn('system', call_args.kwargs)
        self.assertTrue(len(call_args.kwargs['system']) == 1)
        self.assertIn('text', call_args.kwargs['system'][0])

    @patch('service.bedrock_service.DEFAULT_BEDROCK_MODEL_ID', TEST_MODEL_ID)
    def test_should_handle_client_error_appropriately(self):
        # Setup
        self.mock_client.converse.side_effect = ClientError(
            error_response={"Error": {"Message": "Model not found"}},
            operation_name="converse"
        )

        # Execute and Assert
        with self.assertRaises(ClientError):
            self.service.invoke_model(self.test_messages)

    @patch('service.bedrock_service.DEFAULT_BEDROCK_MODEL_ID', TEST_MODEL_ID)
    def test_should_handle_unexpected_errors_appropriately(self):
        # Setup
        self.mock_client.converse.side_effect = Exception("Unexpected error")

        # Execute and Assert
        with self.assertRaises(Exception):
            self.service.invoke_model(self.test_messages)

    @patch('service.bedrock_service.DEFAULT_BEDROCK_MODEL_ID', TEST_MODEL_ID)
    def test_should_concatenate_multiple_content_pieces_correctly(self):
        # Setup
        self.mock_client.converse = Mock(return_value={
            "output": {
                "message": {
                    "content": [
                        {"text": "Hello"},
                        {"text": " "},
                        {"text": "World!"}
                    ]
                }
            },
            "usage": {
                "inputTokens": 10,
                "outputTokens": 20,
                "totalTokens": 30
            },
            "stopReason": "complete"
        })

        # Execute
        result = self.service.invoke_model(self.test_messages)

        # Assert
        self.assertEqual(result, "Hello World!")


if __name__ == '__main__':
    unittest.main()