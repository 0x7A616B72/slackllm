import boto3
from config import logger, DYNAMODB_TABLE_NAME, BEDROCK_MODELS, BedrockModelConfig

class UserPreferencesAccessor:
    def __init__(self):
        self._dynamodb = None
        self._table = None

    @property
    def table(self):
        """Lazy initialization of DynamoDB table."""
        if self._table is None:
            self._dynamodb = boto3.resource("dynamodb")
            self._table = self._dynamodb.Table(DYNAMODB_TABLE_NAME)
        return self._table

    def get_user_model(self, user_id):
        """
        Get the user's preferred model ID.

        Args:
            user_id (str): The Slack user ID.

        Returns:
            str: The user's preferred model ID or None if not set.
        """
        try:
            response = self.table.get_item(Key = {"user_id": user_id})
            return response.get("Item", {}).get("model_id")
        except Exception as e:
            logger.error(f"Error fetching user preferences: {e}")
            return None

    def set_user_model(self, user_id, model_id):
        """
        Set the user's preferred model ID.

        Args:
            user_id (str): The Slack user ID.
            model_id (str): The Bedrock model ID to set as preferred.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Get existing item to preserve other attributes
            response = self.table.get_item(Key={"user_id": user_id})
            item = response.get("Item", {"user_id": user_id})
            
            # Update model_id while preserving other attributes
            item["model_id"] = model_id
            
            # Save back to DynamoDB
            self.table.put_item(Item=item)
            return True
        except Exception as e:
            logger.error(f"Error updating user preferences: {e}")
            return False

    def get_model_display_name(self, model_id: str) -> str:
        """Get the display name for a given model ID."""
        for model in BEDROCK_MODELS:
            if model.arn == model_id:
                return model.description
        return model_id

    def get_available_models(self) -> list[dict]:
        """Get a list of available models with their IDs and display names."""
        return [{"id": model.arn, "name": model.description} for model in BEDROCK_MODELS]

    def get_model_options(self) -> list[dict]:
        """Get a list of model options formatted for Slack's static_select component."""
        return [
            {
                "text": {
                    "type": "plain_text",
                    "text": model.description
                },
                "value": model.arn
            }
            for model in BEDROCK_MODELS
        ]

    def get_user_system_prompt(self, user_id, model_id):
        """
        Get the user's system prompt for a specific model.

        Args:
            user_id (str): The Slack user ID.
            model_id (str): The Bedrock model ID.

        Returns:
            str: The user's system prompt for the model or None if not set.
        """
        try:
            response = self.table.get_item(Key={"user_id": user_id})
            system_prompts = response.get("Item", {}).get("system_prompts", {})
            return system_prompts.get(model_id)
        except Exception as e:
            logger.error(f"Error fetching user system prompt: {e}")
            return None

    def set_user_system_prompt(self, user_id, model_id, system_prompt):
        """
        Set the user's system prompt for a specific model.

        Args:
            user_id (str): The Slack user ID.
            model_id (str): The Bedrock model ID.
            system_prompt (str): The system prompt to set.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Get existing system prompts
            response = self.table.get_item(Key={"user_id": user_id})
            item = response.get("Item", {"user_id": user_id})
            system_prompts = item.get("system_prompts", {})
            
            # Update the system prompt for this model
            system_prompts[model_id] = system_prompt
            item["system_prompts"] = system_prompts
            
            # Save back to DynamoDB
            self.table.put_item(Item=item)
            return True
        except Exception as e:
            logger.error(f"Error updating user system prompt: {e}")
            return False 