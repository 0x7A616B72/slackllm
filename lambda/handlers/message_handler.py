import itertools
from config import logger
from service.bedrock_client import BedrockClient
from service.user_preferences_accessor import UserPreferenceAccessor

class MessageHandler:
    def __init__(self):
        self.bedrock_client = BedrockClient()
        self.user_preferences = UserPreferenceAccessor()

    def handle_message(self, body, say, app_client):
        logger.debug(body)

        bot_user_id = app_client.auth_test()["user_id"]
        message_text = body["event"].get("text", "")
        user_id = body["event"]["user"]

        # Process app mentions in public & private channels
        if f"<@{bot_user_id}>" in message_text:
            self._handle_mention(message_text, bot_user_id, body["event"]["ts"], user_id, say)
            return

        # Process direct messages
        if "thread_ts" not in body["event"] and body["event"]["channel_type"] == "im":
            self._handle_direct_message(message_text, body["event"]["ts"], user_id, say)
            return

        # Process threaded conversations
        thread_ts = body["event"].get("thread_ts")
        if thread_ts:
            self._handle_thread(body["event"], bot_user_id, thread_ts, user_id, say, app_client)
            return

    def _handle_mention(self, message_text, bot_user_id, ts, user_id, say):
        logger.info("Processing app mention")
        message = [
            {
                "role": "user",
                "content": [
                    {"text": message_text.replace(f"<@{bot_user_id}>", "").strip()}
                ],
            }
        ]

        try:
            model_response = self._get_model_response(message, user_id)
            say(model_response, thread_ts=ts)
        except Exception as e:
            logger.error(f"An error occurred while processing the app mention: {str(e)}")
            say(text = f"Error: {str(e)}", thread_ts=ts)

    def _handle_direct_message(self, message_text, ts, user_id, say):
        logger.info("Processing direct message")
        message = [
            {
                "role": "user",
                "content": [{"text": message_text}],
            }
        ]

        try:
            model_response = self._get_model_response(message, user_id)
            say(
                model_response,
                thread_ts = ts,
            )
        except Exception as e:
            logger.error(f"An error occurred while processing direct message: {str(e)}")
            say(text=f"Error: {str(e)}", thread_ts=ts)

    def _handle_thread(self, event, bot_user_id, thread_ts, user_id, say, app_client):
        logger.info("Processing threaded conversation")
        channel = event["channel"]

        try:
            conversation_history = app_client.conversations_replies(
                channel = channel,
                ts = thread_ts,
                limit = 100,
            )

            bot_responded_earlier = any(
                message.get("user") == bot_user_id
                for message in conversation_history["messages"]
                if message.get("user") is not None
            )

            if not bot_responded_earlier:
                logger.info("Bot has not responded earlier in the thread. Skipping processing.")
                return

            messages = [
                {
                    "role": "assistant" if is_assistant else "user",
                    "content": [{"text": " ".join(msg["text"] for msg in group)}]
                }
                for is_assistant, group in itertools.groupby(
                    (m for m in conversation_history["messages"] if m.get("user") is not None),
                    key = lambda m: m.get("user") == bot_user_id
                )
            ]

            model_response = self._get_model_response(messages, user_id)
            say(model_response, thread_ts=thread_ts)

        except Exception as e:
            logger.error(f"Error while processing threaded conversation: {str(e)}")
            say(text=f"Error: {str(e)}", thread_ts=thread_ts)

    def _get_model_response(self, messages, user_id):
        user_model = self.user_preferences.get_user_model(user_id)
        return self.bedrock_client.invoke_model(messages, user_model) 