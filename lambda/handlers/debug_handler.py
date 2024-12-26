import os
from config import logger

class DebugHandler:
    @staticmethod
    def handle_debug_message(message, say):
        """
        Handles debug messages and returns system information.

        Args:
            message (dict): The message event from Slack.
            say (function): A function to send a response message.
        """
        logger.info(f"Received debug message: {message['text']}")
        
        # Collect debug information
        debug_info = {
            "Bedrock model ID": os.environ.get("BEDROCK_MODEL_ID"),
            "Lambda function name": os.environ.get("AWS_LAMBDA_FUNCTION_NAME"),
            "Lambda function version": os.environ.get("AWS_LAMBDA_FUNCTION_VERSION"),
            "Lambda region": os.environ.get("AWS_REGION"),
            "Lambda memory limit (MB)": os.environ.get("AWS_LAMBDA_FUNCTION_MEMORY_SIZE"),
            "Lambda log group name": os.environ.get("AWS_LAMBDA_LOG_GROUP_NAME")
        }

        # Log debug info
        for key, value in debug_info.items():
            logger.info(f"{key}: {value}")

        # Format message for Slack
        formatted_message = "\n".join(
            f"*{key}:* {value}" for key, value in debug_info.items()
        )

        say(formatted_message, thread_ts=message["ts"]) 