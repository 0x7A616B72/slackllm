import boto3
import datetime
from botocore.exceptions import ClientError
from config import logger, DEFAULT_BEDROCK_MODEL_ID, BEDROCK_MODELS
from service.user_preferences_accessor import UserPreferencesAccessor

class BedrockService:
    def __init__(self):
        self.client = boto3.client("bedrock-runtime")
        self.user_preferences = UserPreferencesAccessor()

    def invoke_model(self, messages, model_id=None, user_id=None):
        """
        Invokes a bedrock model using the provided messages.

        Args:
            messages (list): A list of messages to be sent to the model.
            model_id (str, optional): The specific model ID to use. Defaults to None.
            user_id (str, optional): The Slack user ID. Defaults to None.

        Returns:
            str: The output text generated by the model.

        Raises:
            ClientError: If there's an error invoking the Bedrock model.
        """
        try:
            model_id = model_id or DEFAULT_BEDROCK_MODEL_ID
            logger.info(f"Invoking model {model_id} with {len(messages)} messages.")

            system_prompt = None
            if user_id:
                system_prompt = self.user_preferences.get_user_system_prompt(user_id, model_id)

            # If no custom system prompt, use default for this model
            if not system_prompt:
                system_prompt = self._get_default_system_prompt(model_id)
            else:
                # Replace datetime placeholder with current UTC time
                current_utc = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
                system_prompt = system_prompt.replace("{datetime}", current_utc)
            logger.info(f"Latest message text: {messages[-1]['content'][0]['text']}")
            logger.info(f"Using system prompt: {system_prompt}")
            
            # Check if this is the Claude 3.7 Sonnet Reasoning model
            is_sonnet_reasoning = self._is_sonnet_reasoning_model(model_id)
            
            # Prepare converse parameters
            converse_params = {
                "messages": messages,
                "modelId": model_id,
                "system": [{"text": system_prompt}],
            }
            
            # Add thinking configuration for Claude 3.7 Sonnet Reasoning
            if is_sonnet_reasoning:
                logger.info("Using extended thinking mode for Claude 3.7 Sonnet Reasoning")
                converse_params["inferenceConfig"] = {"maxTokens": 64000}
                converse_params["additionalModelRequestFields"] = {
                    "thinking": {
                        "type": "enabled",
                        "budget_tokens": 48000, # needs to be less than maxTokens
                    }
                }
            
            # Invoke the model
            response = self.client.converse(**converse_params)
            logger.info(f"Model response: {response}")
            
            # Process the response
            if is_sonnet_reasoning:
                output_text = self._process_reasoning_response(response)
            else:
                output_text = "".join(
                    content["text"] for content in response["output"]["message"]["content"]
                )

            self._log_usage_metrics(response)
            return output_text

        except ClientError as e:
            logger.error(f"ERROR: Can't invoke '{model_id}'. Reason: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error occurred: {e}")
            raise

    def _process_reasoning_response(self, response):
        """
        Process the response from Claude 3.7 Sonnet Reasoning model.
        Extracts both reasoning text and standard text, formatting reasoning as quoted messages.
        
        Args:
            response (dict): The response from the Bedrock Converse API.
            
        Returns:
            str: The formatted output text with reasoning as quoted messages.
        """
        output_text = ""
        standard_text = ""
        
        # Process each content block
        for block in response["output"]["message"]["content"]:
            if "text" in block:
                standard_text = block["text"]
            elif "reasoningContent" in block:
                # Extract thinking/reasoning text
                thinking_text = block["reasoningContent"]["reasoningText"]["text"]
                
                # Format thinking text as quoted messages in Slack markdown
                # Split by newlines and format each paragraph as a quote
                thinking_paragraphs = thinking_text.split("\n\n")
                for paragraph in thinking_paragraphs:
                    if paragraph.strip():
                        # Format as Slack quote (> at the beginning of each line)
                        formatted_paragraph = "\n".join([f"> {line}" for line in paragraph.split("\n")])
                        output_text += f"{formatted_paragraph}\n\n"
        
        # Add the standard response text after the thinking blocks
        output_text += standard_text
        
        return output_text
        
    def _is_sonnet_reasoning_model(self, model_id):
        """
        Check if the model is Claude 3.7 Sonnet Reasoning.
        
        Args:
            model_id (str): The model ID to check.
            
        Returns:
            bool: True if the model is Claude 3.7 Sonnet Reasoning, False otherwise.
        """
        # Check if the model is Claude 3.7 Sonnet
        is_sonnet_37 = "claude-3-7-sonnet" in model_id
        
        # Check if this is the Reasoning configuration
        for model in BEDROCK_MODELS:
            if model.arn == model_id and "Reasoning" in model.description and is_sonnet_37:
                return True
        
        return False
    
    def _log_usage_metrics(self, response):
        """Log token usage and other metrics from the model response."""
        token_usage = response["usage"]
        logger.info(f"Input tokens: {token_usage['inputTokens']}")
        logger.info(f"Output tokens: {token_usage['outputTokens']}")
        logger.info(f"Total tokens: {token_usage['totalTokens']}")
        logger.info(f"Stop reason: {response['stopReason']}")

    def _get_default_system_prompt(self, model_id=None):
        """Returns the default system prompt for the specified model."""
        # If model_id is provided, try to get its specific default prompt
        if model_id:
            for model in BEDROCK_MODELS:
                if model.arn == model_id:
                    if model.default_system_prompt:
                        current_utc = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
                        return model.default_system_prompt.replace("{datetime}", current_utc)
                    break

        # Fallback to generic prompt if no model-specific prompt found
        return f"You are a helpful AI assistant. The current time is {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")}."
