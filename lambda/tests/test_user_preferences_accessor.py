import unittest
from unittest.mock import Mock, patch
from botocore.exceptions import ClientError
from service.user_preferences_accessor import UserPreferencesAccessor
from config import BEDROCK_MODELS

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

    def test_get_model_display_name_found(self):
        # Setup - using first model from BEDROCK_MODELS
        test_model_id, expected_name = BEDROCK_MODELS[0]

        # Execute
        result = self.accessor.get_model_display_name(test_model_id)

        # Assert
        self.assertEqual(result, expected_name)

    def test_get_model_display_name_not_found(self):
        # Execute
        result = self.accessor.get_model_display_name("non-existent-model")

        # Assert
        self.assertEqual(result, "Not set")

    def test_get_model_options(self):
        # Execute
        result = self.accessor.get_model_options()

        # Assert
        self.assertEqual(len(result), len(BEDROCK_MODELS))
        for i, (model_id, display_name) in enumerate(BEDROCK_MODELS):
            self.assertEqual(result[i]["text"]["type"], "plain_text")
            self.assertEqual(result[i]["text"]["text"], display_name)
            self.assertEqual(result[i]["value"], model_id)

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

if __name__ == '__main__':
    unittest.main() 