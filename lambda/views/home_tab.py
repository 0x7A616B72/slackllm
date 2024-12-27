from config import logger
from service.user_preferences_accessor import UserPreferencesAccessor

class HomeTab:
    def __init__(self):
        self.user_preferences_accessor = UserPreferencesAccessor()

    def update_view(self, client, user_id):
        try:
            current_model_id = self.user_preferences_accessor.get_user_model(user_id)
            current_model_display = self.user_preferences_accessor.get_model_display_name(current_model_id)
            current_system_prompt = self.user_preferences_accessor.get_user_system_prompt(user_id, current_model_id) if current_model_id else None

            client.views_publish(
                user_id=user_id,
                view=self._get_view_payload(current_model_display, current_model_id, current_system_prompt)
            )
        except Exception as e:
            logger.error(f"Error publishing home tab: {e}")

    def _get_view_payload(self, current_model_display, current_model_id, current_system_prompt):
        blocks = [
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
                        "options": self.user_preferences_accessor.get_model_options(),
                        "action_id": "select_model",
                    }
                ],
            },
        ]

        # Only show system prompt section if a model is selected
        if current_model_id:
            blocks.extend([
                {"type": "divider"},
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "System Prompt",
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Customize the system prompt for this model. Use `{datetime}` as a placeholder for the current UTC time.",
                    },
                },
                {
                    "type": "input",
                    "block_id": "system_prompt_block",
                    "element": {
                        "type": "plain_text_input",
                        "multiline": True,
                        "action_id": "system_prompt_input",
                        "initial_value": current_system_prompt or "",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Enter your system prompt here..."
                        }
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "System Prompt"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Save System Prompt"
                            },
                            "style": "primary",
                            "action_id": "save_system_prompt"
                        }
                    ]
                }
            ])

        return {
            "type": "home",
            "callback_id": "home_view",
            "blocks": blocks,
        } 