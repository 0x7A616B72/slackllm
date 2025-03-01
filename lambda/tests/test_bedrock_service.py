import unittest
from unittest.mock import Mock, patch
from botocore.exceptions import ClientError
from service.bedrock_service import BedrockService
from config import BedrockModelConfig

TEST_MODEL_ID = "test.model.id"
ALTERNATE_MODEL_ID = "alternate.model.id"
SONNET_REASONING_MODEL_ID = "arn:aws:bedrock:us-east-1:705478596818:inference-profile/us.anthropic.claude-3-7-sonnet-20250219-v1:0"

class TestBedrockService(unittest.TestCase):
    @patch('boto3.client')
    @patch('service.bedrock_service.UserPreferencesAccessor')
    def setUp(self, mock_prefs, mock_boto3_client):
        self.mock_client = Mock()
        mock_boto3_client.return_value = self.mock_client
        self.mock_prefs = mock_prefs
        self.mock_prefs_instance = mock_prefs.return_value
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
    @patch('service.bedrock_service.BEDROCK_MODELS', [
        BedrockModelConfig(
            arn=TEST_MODEL_ID,
            description="Test Model",
            default_system_prompt="You are Test Model. The current time is {datetime}."
        )
    ])
    def test_should_use_model_specific_system_prompt(self):
        # Setup
        self.mock_client.converse = Mock(return_value=self.mock_response)
        self.mock_prefs_instance.get_user_system_prompt.return_value = None

        # Execute
        result = self.service.invoke_model(self.test_messages)

        # Assert
        self.assertEqual(result, "Hello there!")
        
        # Get the actual call arguments
        call_args = self.mock_client.converse.call_args
        
        # Assert the messages and modelId match exactly
        self.assertEqual(call_args.kwargs['messages'], self.test_messages)
        self.assertEqual(call_args.kwargs['modelId'], TEST_MODEL_ID)
        
        # Assert the system prompt contains the model-specific text
        self.assertIn('system', call_args.kwargs)
        self.assertTrue(len(call_args.kwargs['system']) == 1)
        self.assertIn('text', call_args.kwargs['system'][0])
        self.assertIn("You are Test Model", call_args.kwargs['system'][0]['text'])
        self.assertIn("UTC", call_args.kwargs['system'][0]['text'])

    @patch('service.bedrock_service.DEFAULT_BEDROCK_MODEL_ID', TEST_MODEL_ID)
    @patch('service.bedrock_service.BEDROCK_MODELS', [
        BedrockModelConfig(
            arn=TEST_MODEL_ID,
            description="Test Model",
            default_system_prompt=""  # Empty default prompt
        )
    ])
    def test_should_use_fallback_system_prompt_when_no_model_default(self):
        # Setup
        self.mock_client.converse = Mock(return_value=self.mock_response)
        self.mock_prefs_instance.get_user_system_prompt.return_value = None

        # Execute
        result = self.service.invoke_model(self.test_messages)

        # Assert
        self.assertEqual(result, "Hello there!")
        
        # Get the actual call arguments
        call_args = self.mock_client.converse.call_args
        
        # Assert the system prompt contains the fallback text
        self.assertIn('system', call_args.kwargs)
        self.assertTrue(len(call_args.kwargs['system']) == 1)
        self.assertIn('text', call_args.kwargs['system'][0])
        self.assertIn("You are a helpful AI assistant", call_args.kwargs['system'][0]['text'])
        self.assertIn("UTC", call_args.kwargs['system'][0]['text'])

    @patch('service.bedrock_service.DEFAULT_BEDROCK_MODEL_ID', TEST_MODEL_ID)
    def test_should_use_custom_system_prompt(self):
        # Setup
        self.mock_client.converse = Mock(return_value=self.mock_response)
        test_user_id = "test_user"
        custom_prompt = "Custom system prompt with {datetime}"
        self.mock_prefs_instance.get_user_system_prompt.return_value = custom_prompt

        # Execute
        result = self.service.invoke_model(self.test_messages, user_id=test_user_id)

        # Assert
        self.assertEqual(result, "Hello there!")
        
        # Get the actual call arguments
        call_args = self.mock_client.converse.call_args
        
        # Assert the messages and modelId match exactly
        self.assertEqual(call_args.kwargs['messages'], self.test_messages)
        self.assertEqual(call_args.kwargs['modelId'], TEST_MODEL_ID)
        
        # Assert the system prompt is the custom one with datetime replaced
        self.assertIn('system', call_args.kwargs)
        self.assertTrue(len(call_args.kwargs['system']) == 1)
        self.assertIn('text', call_args.kwargs['system'][0])
        system_prompt = call_args.kwargs['system'][0]['text']
        self.assertTrue(system_prompt.startswith("Custom system prompt with "))
        self.assertIn("UTC", system_prompt)
        self.assertNotIn("{datetime}", system_prompt)

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

    @patch('service.bedrock_service.BEDROCK_MODELS', [
        BedrockModelConfig(
            arn=SONNET_REASONING_MODEL_ID,
            description="Anthropic Claude 3.7 Sonnet Reasoning (Text, Image, Document)",
            default_system_prompt="You are Claude 3.7 Sonnet Reasoning."
        ),
        BedrockModelConfig(
            arn="arn:aws:bedrock:us-east-1:705478596818:inference-profile/us.anthropic.claude-3-5-sonnet-20241022-v2:0",
            description="Anthropic Claude 3.5 Sonnet V2 (Text, Image, Document)",
            default_system_prompt="You are Claude 3.5 Sonnet."
        )
    ])
    def test_is_sonnet_reasoning_model_should_identify_correctly(self):
        # Test with Sonnet 3.7 Reasoning model
        self.assertTrue(self.service._is_sonnet_reasoning_model(SONNET_REASONING_MODEL_ID))
        
        # Test with non-reasoning model
        self.assertFalse(self.service._is_sonnet_reasoning_model("arn:aws:bedrock:us-east-1:705478596818:inference-profile/us.anthropic.claude-3-5-sonnet-20241022-v2:0"))
        
        # Test with non-Sonnet model
        self.assertFalse(self.service._is_sonnet_reasoning_model("arn:aws:bedrock:us-east-1:705478596818:inference-profile/us.amazon.nova-pro-v1:0"))

    def test_process_reasoning_response_should_format_correctly(self):
        # Setup a mock response with reasoning content
        mock_response = {
            "output": {
                "message": {
                    "content": [
                        {"text": "Final answer"},
                        {"reasoningContent": {
                            "reasoningText": {
                                "text": "First thinking paragraph.\nWith multiple lines.\n\nSecond thinking paragraph."
                            }
                        }}
                    ]
                }
            },
            "usage": {
                "inputTokens": 10,
                "outputTokens": 20,
                "totalTokens": 30
            },
            "stopReason": "complete"
        }
        
        # Execute
        result = self.service._process_reasoning_response(mock_response)
        
        # Assert
        expected_output = "> First thinking paragraph.\n> With multiple lines.\n\n> Second thinking paragraph.\n\nFinal answer"
        self.assertEqual(result, expected_output)

    @patch('service.bedrock_service.BEDROCK_MODELS', [
        BedrockModelConfig(
            arn=SONNET_REASONING_MODEL_ID,
            description="Anthropic Claude 3.7 Sonnet Reasoning (Text, Image, Document)",
            default_system_prompt="You are Claude 3.7 Sonnet Reasoning."
        )
    ])
    def test_invoke_model_should_add_thinking_config_for_sonnet_reasoning(self):
        # Setup
        self.mock_client.converse = Mock(return_value={
            "output": {
                "message": {
                    "content": [
                        {"text": "Final answer"},
                        {"reasoningContent": {
                            "reasoningText": {
                                "text": "Thinking process"
                            }
                        }}
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
        result = self.service.invoke_model(self.test_messages, model_id=SONNET_REASONING_MODEL_ID)
        
        # Assert
        call_args = self.mock_client.converse.call_args
        
        # Check that thinking configuration was added
        self.assertIn('inferenceConfig', call_args.kwargs)
        
        self.assertIn('additionalModelRequestFields', call_args.kwargs)
        self.assertIn('thinking', call_args.kwargs['additionalModelRequestFields'])
        
        # Verify thinking configuration structure (type and budget_tokens)
        thinking_config = call_args.kwargs['additionalModelRequestFields']['thinking']
        self.assertEqual(thinking_config["type"], "enabled")
        self.assertIn("budget_tokens", thinking_config)
        self.assertIsInstance(thinking_config["budget_tokens"], int)
        
        # Check that the response was processed correctly
        self.assertEqual(result, "> Thinking process\n\nFinal answer")

    @patch('service.bedrock_service.BEDROCK_MODELS', [
        BedrockModelConfig(
            arn="arn:aws:bedrock:us-east-1:705478596818:inference-profile/us.anthropic.claude-3-5-sonnet-20241022-v2:0",
            description="Anthropic Claude 3.5 Sonnet V2 (Text, Image, Document)",
            default_system_prompt="You are Claude 3.5 Sonnet."
        )
    ])
    def test_invoke_model_should_not_add_thinking_config_for_non_reasoning_models(self):
        # Setup
        self.mock_client.converse = Mock(return_value=self.mock_response)
        non_reasoning_model = "arn:aws:bedrock:us-east-1:705478596818:inference-profile/us.anthropic.claude-3-5-sonnet-20241022-v2:0"
        
        # Execute
        result = self.service.invoke_model(self.test_messages, model_id=non_reasoning_model)
        
        # Assert
        call_args = self.mock_client.converse.call_args
        
        # Check that thinking configuration was not added
        self.assertNotIn('inferenceConfig', call_args.kwargs)
        self.assertNotIn('additionalModelRequestFields', call_args.kwargs)
        
        # Check that the response was processed correctly
        self.assertEqual(result, "Hello there!")

if __name__ == '__main__':
    unittest.main()
