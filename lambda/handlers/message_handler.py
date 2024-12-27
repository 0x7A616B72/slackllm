import base64
import itertools
from config import logger
from service.bedrock_service import BedrockService
from service.user_preferences_accessor import UserPreferencesAccessor
from service.message_preparation_helper import MessagePreparationHelper

class MessageHandler:
    def __init__(self):
        self.bedrock_service = BedrockService()
        self.user_preferences_accessor = UserPreferencesAccessor()
        self.message_preparation_helper = MessagePreparationHelper()

    def handle_message(self, body, say, app_client):
        bot_user_id = app_client.auth_test()["user_id"]
        message_text = body["event"].get("text", "")
        user_id = body["event"]["user"]
        files = body["event"].get("files", [])
        logger.info(f"Processing message from user {user_id} with {len(files)} files")

        # Process app mentions in public & private channels
        if f"<@{bot_user_id}>" in message_text:
            self._handle_mention(message_text, bot_user_id, body["event"]["ts"], user_id, say, files, app_client)
            return

        # Process direct messages
        if "thread_ts" not in body["event"] and body["event"]["channel_type"] == "im":
            self._handle_direct_message(message_text, body["event"]["ts"], user_id, say, files, app_client)
            return

        # Process threaded conversations
        thread_ts = body["event"].get("thread_ts")
        if thread_ts:
            self._handle_thread(body["event"], bot_user_id, thread_ts, user_id, say, app_client)
            return

    def _handle_mention(self, message_text, bot_user_id, ts, user_id, say, files, app_client):
        logger.info("Processing app mention")
        try:
            message = self.message_preparation_helper.prepare_message(
                message_text.replace(f"<@{bot_user_id}>", "").strip(), 
                files, 
                app_client
            )
            model_response = self._get_model_response([message], user_id)
            say(model_response, thread_ts=ts)
        except Exception as e:
            logger.error(f"An error occurred while processing the app mention: {str(e)}")
            say(text=f"Error: {str(e)}", thread_ts=ts)

    def _handle_direct_message(self, message_text, ts, user_id, say, files, app_client):
        logger.info("Processing direct message")
        try:
            message = self.message_preparation_helper.prepare_message(message_text, files, app_client)
            model_response = self._get_model_response([message], user_id)
            say(model_response, thread_ts=ts)
        except Exception as e:
            logger.error(f"An error occurred while processing direct message: {str(e)}")
            say(text=f"Error: {str(e)}", thread_ts=ts)

    def _handle_thread(self, event, bot_user_id, thread_ts, user_id, say, app_client):
        logger.info("Processing threaded conversation")
        channel = event["channel"]

        try:
            conversation_history = app_client.conversations_replies(
                channel=channel,
                ts=thread_ts,
                limit=100,
            )

            bot_responded_earlier = any(
                message.get("user") == bot_user_id
                for message in conversation_history["messages"]
                if message.get("user") is not None
            )

            if not bot_responded_earlier:
                logger.info("Bot has not responded earlier in the thread. Skipping processing.")
                return

            # Group messages by user and prepare them with files
            messages = []
            for is_assistant, group in itertools.groupby(
                (m for m in conversation_history["messages"] if m.get("user") is not None),
                key=lambda m: m.get("user") == bot_user_id
            ):
                group_messages = list(group)
                # Concatenate text from all messages in the group
                combined_text = " ".join(msg.get("text", "") for msg in group_messages)
                
                # Get files from all messages in the group
                all_files = []
                for msg in group_messages:
                    if msg.get("files"):
                        all_files.extend(msg.get("files"))

                # Prepare the message with text and files
                prepared_message = self.message_preparation_helper.prepare_message(combined_text, all_files, app_client)
                prepared_message["role"] = "assistant" if is_assistant else "user"
                messages.append(prepared_message)

            model_response = self._get_model_response(messages, user_id)
            say(model_response, thread_ts=thread_ts)

        except Exception as e:
            logger.error(f"Error while processing threaded conversation: {str(e)}")
            say(text=f"Error: {str(e)}", thread_ts=thread_ts)

    def _get_model_response(self, messages, user_id):
        user_model = self.user_preferences_accessor.get_user_model(user_id)
        return self.bedrock_service.invoke_model(messages, user_model) 