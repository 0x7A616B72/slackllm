import unittest
from unittest.mock import Mock, patch
from botocore.exceptions import ClientError
from service.user_preferences_accessor import UserPreferencesAccessor
from config import BEDROCK_MODELS, BedrockModelConfig

class TestUserPreferencesAccessor(unittest.TestCase):
    def setUp(self):
        self.accessor = UserPreferencesAccessor()
        self.test_user_id = "U123456"
        self.test_model_id = "model-123"

    @patch('boto3.resource')
    def test_table_lazy_initialization(self, mock_boto3_resource):
        # Setup
        mock_table = Mock()
        mock_dynamodb = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3_resource.return_value = mock_dynamodb

        # Execute - first access
        table1 = self.accessor.table

        # Assert first access
        mock_boto3_resource.assert_called_once_with("dynamodb")
        mock_dynamodb.Table.assert_called_once()

        # Execute - second access
        table2 = self.accessor.table

        # Assert second access doesn't create new resources
        self.assertEqual(mock_boto3_resource.call_count, 1)
        self.assertEqual(mock_dynamodb.Table.call_count, 1)
        self.assertEqual(table1, table2)

    @patch('boto3.resource')
    def test_get_user_model_success(self, mock_boto3_resource):
        # Setup
        mock_table = Mock()
        mock_table.get_item.return_value = {
            "Item": {"user_id": self.test_user_id, "model_id": self.test_model_id}
        }
        mock_dynamodb = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3_resource.return_value = mock_dynamodb

        # Execute
        result = self.accessor.get_user_model(self.test_user_id)

        # Assert
        self.assertEqual(result, self.test_model_id)
        mock_table.get_item.assert_called_once_with(Key={"user_id": self.test_user_id})

    @patch('boto3.resource')
    def test_get_user_model_not_found(self, mock_boto3_resource):
        # Setup
        mock_table = Mock()
        mock_table.get_item.return_value = {}
        mock_dynamodb = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3_resource.return_value = mock_dynamodb

        # Execute
        result = self.accessor.get_user_model(self.test_user_id)

        # Assert
        self.assertIsNone(result)
        mock_table.get_item.assert_called_once_with(Key={"user_id": self.test_user_id})

    @patch('boto3.resource')
    def test_get_user_model_error(self, mock_boto3_resource):
        # Setup
        mock_table = Mock()
        mock_table.get_item.side_effect = Exception("DynamoDB error")
        mock_dynamodb = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3_resource.return_value = mock_dynamodb

        # Execute
        result = self.accessor.get_user_model(self.test_user_id)

        # Assert
        self.assertIsNone(result)
        mock_table.get_item.assert_called_once_with(Key={"user_id": self.test_user_id})

    @patch('boto3.resource')
    def test_set_user_model_success(self, mock_boto3_resource):
        # Setup
        mock_table = Mock()
        mock_table.get_item.return_value = {
            "Item": {
                "user_id": self.test_user_id,
                "system_prompts": {"existing-model": "existing prompt"}
            }
        }
        mock_dynamodb = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3_resource.return_value = mock_dynamodb

        # Execute
        result = self.accessor.set_user_model(self.test_user_id, self.test_model_id)

        # Assert
        self.assertTrue(result)
        mock_table.get_item.assert_called_once_with(Key={"user_id": self.test_user_id})
        mock_table.put_item.assert_called_once_with(
            Item={
                "user_id": self.test_user_id,
                "model_id": self.test_model_id,
                "system_prompts": {"existing-model": "existing prompt"}
            }
        )

    @patch('boto3.resource')
    def test_set_user_model_error(self, mock_boto3_resource):
        # Setup
        mock_table = Mock()
        mock_table.get_item.return_value = {"Item": {"user_id": self.test_user_id}}
        mock_table.put_item.side_effect = Exception("DynamoDB error")
        mock_dynamodb = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3_resource.return_value = mock_dynamodb

        # Execute
        result = self.accessor.set_user_model(self.test_user_id, self.test_model_id)

        # Assert
        self.assertFalse(result)
        mock_table.get_item.assert_called_once_with(Key={"user_id": self.test_user_id})
        mock_table.put_item.assert_called_once_with(
            Item={"user_id": self.test_user_id, "model_id": self.test_model_id}
        )

    def test_get_model_display_name(self):
        # Setup - using first model from BEDROCK_MODELS
        test_model = BEDROCK_MODELS[0]
        accessor = UserPreferencesAccessor()

        # Test
        result = accessor.get_model_display_name(test_model.arn)

        # Assert
        self.assertEqual(result, test_model.description)

    def test_get_available_models(self):
        # Setup
        accessor = UserPreferencesAccessor()

        # Test
        result = accessor.get_available_models()

        # Assert
        self.assertEqual(len(result), len(BEDROCK_MODELS))
        for i, model in enumerate(BEDROCK_MODELS):
            self.assertEqual(result[i]["id"], model.arn)
            self.assertEqual(result[i]["name"], model.description)

    @patch('boto3.resource')
    def test_get_user_system_prompt_success(self, mock_boto3_resource):
        # Setup
        mock_table = Mock()
        mock_table.get_item.return_value = {
            "Item": {
                "user_id": self.test_user_id,
                "system_prompts": {
                    self.test_model_id: "Test system prompt"
                }
            }
        }
        mock_dynamodb = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3_resource.return_value = mock_dynamodb

        # Execute
        result = self.accessor.get_user_system_prompt(self.test_user_id, self.test_model_id)

        # Assert
        self.assertEqual(result, "Test system prompt")
        mock_table.get_item.assert_called_once_with(Key={"user_id": self.test_user_id})

    @patch('boto3.resource')
    def test_get_user_system_prompt_not_found(self, mock_boto3_resource):
        # Setup
        mock_table = Mock()
        mock_table.get_item.return_value = {
            "Item": {
                "user_id": self.test_user_id,
                "system_prompts": {}
            }
        }
        mock_dynamodb = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3_resource.return_value = mock_dynamodb

        # Execute
        result = self.accessor.get_user_system_prompt(self.test_user_id, self.test_model_id)

        # Assert
        self.assertIsNone(result)
        mock_table.get_item.assert_called_once_with(Key={"user_id": self.test_user_id})

    @patch('boto3.resource')
    def test_set_user_system_prompt_success(self, mock_boto3_resource):
        # Setup
        mock_table = Mock()
        mock_table.get_item.return_value = {
            "Item": {
                "user_id": self.test_user_id,
                "system_prompts": {}
            }
        }
        mock_dynamodb = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3_resource.return_value = mock_dynamodb

        # Execute
        result = self.accessor.set_user_system_prompt(
            self.test_user_id,
            self.test_model_id,
            "New system prompt"
        )

        # Assert
        self.assertTrue(result)
        mock_table.put_item.assert_called_once_with(
            Item={
                "user_id": self.test_user_id,
                "system_prompts": {self.test_model_id: "New system prompt"}
            }
        )

    @patch('boto3.resource')
    def test_set_user_system_prompt_error(self, mock_boto3_resource):
        # Setup
        mock_table = Mock()
        mock_table.get_item.return_value = {
            "Item": {
                "user_id": self.test_user_id,
                "system_prompts": {}
            }
        }
        mock_table.put_item.side_effect = Exception("DynamoDB error")
        mock_dynamodb = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3_resource.return_value = mock_dynamodb

        # Execute
        result = self.accessor.set_user_system_prompt(
            self.test_user_id,
            self.test_model_id,
            "New system prompt"
        )

        # Assert
        self.assertFalse(result)

    @patch('boto3.resource')
    def test_set_user_model_preserves_other_model_prompts(self, mock_boto3_resource):
        # Setup
        mock_table = Mock()
        mock_table.get_item.return_value = {
            "Item": {
                "user_id": self.test_user_id,
                "model_id": "old-model",
                "system_prompts": {
                    "old-model": "Old model prompt",
                    "other-model": "Other model prompt"
                }
            }
        }
        mock_dynamodb = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3_resource.return_value = mock_dynamodb

        # Execute
        result = self.accessor.set_user_model(self.test_user_id, self.test_model_id)

        # Assert
        self.assertTrue(result)
        mock_table.get_item.assert_called_once_with(Key={"user_id": self.test_user_id})
        mock_table.put_item.assert_called_once_with(
            Item={
                "user_id": self.test_user_id,
                "model_id": self.test_model_id,
                "system_prompts": {
                    "old-model": "Old model prompt",
                    "other-model": "Other model prompt"
                }
            }
        )

    def test_get_model_options(self):
        # Execute
        options = self.accessor.get_model_options()

        # Assert
        self.assertIsInstance(options, list)
        for option in options:
            self.assertIn("text", option)
            self.assertIn("value", option)
            self.assertEqual(option["text"]["type"], "plain_text")
            self.assertIsInstance(option["text"]["text"], str)
            self.assertIsInstance(option["value"], str)

if __name__ == '__main__':
    unittest.main() 