import os
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Slack configuration
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")

# AWS configuration
DYNAMODB_TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME")
DEFAULT_BEDROCK_MODEL_ID = os.environ.get("BEDROCK_MODEL_ID")

# Bedrock model configurations
BEDROCK_MODELS = [
    (
        "arn:aws:bedrock:us-east-1:705478596818:inference-profile/us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        "Anthropic Claude 3.5 Sonnet V2"
    ),
    (
        "arn:aws:bedrock:us-east-1:705478596818:inference-profile/us.anthropic.claude-3-5-haiku-20241022-v1:0",
        "Anthropic Claude 3.5 Haiku"
    ),
] 