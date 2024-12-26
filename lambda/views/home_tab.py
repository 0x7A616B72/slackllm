from config import logger
from service.user_preferences_accessor import UserPreferencesAccessor

class HomeTab:
    def __init__(self):
        self.user_preferences = UserPreferencesAccessor()

    def update_view(self, client, user_id):
        try:
            current_model_id = self.user_preferences.get_user_model(user_id)
            current_model_display = self.user_preferences.get_model_display_name(current_model_id)

            client.views_publish(
                user_id=user_id,
                view=self._get_view_payload(current_model_display)
            )
        except Exception as e:
            logger.error(f"Error publishing home tab: {e}")

    def _get_view_payload(self, current_model_display):
        return {
            "type": "home",
            "callback_id": "home_view",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "Welcome to SlackLLM!",
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*SlackLLM* is a conversational AI assistant powered by Amazon Bedrock.",
                    },
                },
                {"type": "divider"},
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "Choose your model",
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"Your current Bedrock model: *{current_model_display}*",
                    },
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": "Choose your preferred Bedrock model from the dropdown below.",
                        }
                    ],
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "static_select",
                            "placeholder": {
                                "type": "plain_text",
                                "text": "Select a Bedrock model",
                            },
                            "options": self.user_preferences.get_model_options(),
                            "action_id": "select_model",
                        }
                    ],
                },
            ],
        } 