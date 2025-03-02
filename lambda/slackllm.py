from slack_bolt import App
from slack_bolt.adapter.aws_lambda import SlackRequestHandler

from config import logger, SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET
from handlers.message_handler import MessageHandler
from handlers.debug_handler import DebugHandler
from views.home_tab import HomeTab
from service.user_preferences_accessor import UserPreferencesAccessor
from service.bedrock_service import BedrockService

# Initialize the Slack app
app = App(
    token = SLACK_BOT_TOKEN,
    signing_secret = SLACK_SIGNING_SECRET,
    process_before_response = True,
)

# Initialize handlers
message_handler = MessageHandler()
home_tab = HomeTab()
user_preferences = UserPreferencesAccessor()
bedrock_service = BedrockService()

def send_ack_to_slack(body, ack):
    """Acknowledge the request within 3 seconds, this is required by Slack."""
    ack()
    logger.debug(body)

# Message event handlers
def handle_message(body, say, client):
    message_handler.handle_message(body, say, client)

# Handle message events lazily so we can send an ack to Slack within 3 seconds
app.event("message")(ack=send_ack_to_slack, lazy=[handle_message])

@app.message(":bug:")
def handle_debug_message(message, say):
    DebugHandler.handle_debug_message(message, say)

# Home tab handlers
@app.event("app_home_opened")
def update_home_tab_handler(client, event):
    home_tab.update_view(client, event["user"])

# Model selection handlers
@app.action("select_model")
def handle_model_selection(ack, body, client):
    ack()
    user_id = body["user"]["id"]
    selected_model = body["actions"][0]["selected_option"]["value"]
    selected_model_display = body["actions"][0]["selected_option"]["text"]["text"]

    try:
        # Set the user's model preference
        if user_preferences.set_user_model(user_id, selected_model):
            # Update the home tab view using the client directly
            home_tab.update_view(client, user_id)
            
            # Send confirmation message
            client.chat_postMessage(
                channel=user_id,
                text=f"Your Bedrock model preference has been updated to: *{selected_model_display}*"
            )
    except Exception as e:
        logger.error(f"Error updating model preference: {e}")
        client.chat_postMessage(
            channel=user_id,
            text="There was an error updating your model preference. Please try again later."
        )

@app.action("save_system_prompt")
def handle_save_system_prompt(ack, body, client):
    ack()
    user_id = body["user"]["id"]
    current_model = user_preferences.get_user_model(user_id)
    
    try:
        # Get the system prompt from the input block
        system_prompt = body["view"]["state"]["values"]["system_prompt_block"]["system_prompt_input"]["value"]
        
        if user_preferences.set_user_system_prompt(user_id, current_model, system_prompt):
            home_tab.update_view(client, user_id)
            client.chat_postMessage(
                channel=user_id,
                text="Your system prompt has been updated."
            )
    except Exception as e:
        logger.error(f"Error saving system prompt: {e}")
        client.chat_postMessage(
            channel=user_id,
            text="There was an error saving your system prompt. Please try again later."
        )

@app.error
def custom_error_handler(error, body):
    logger.exception(f"Error: {error}")
    logger.info(f"Request body: {body}")

def lambda_handler(event, context):
    slack_handler = SlackRequestHandler(app=app)
    return slack_handler.handle(event, context)
