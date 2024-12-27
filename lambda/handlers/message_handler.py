import base64
import itertools
from config import logger
from service.bedrock_service import BedrockService
from service.file_service import FileService
from service.user_preferences_accessor import UserPreferencesAccessor

class MessageHandler:
    # Supported file types
    SUPPORTED_IMAGE_TYPES = ["png", "jpg", "jpeg", "gif", "webp"]
    SUPPORTED_VIDEO_TYPES = ["mov", "mkv", "mp4", "webm", "flv", "mpeg", "mpg", "wmv", "three_gp"]
    SUPPORTED_DOCUMENT_TYPES = ["pdf", "csv", "doc", "docx", "xls", "xlsx", "html", "txt", "md"]

    def __init__(self):
        self.bedrock_service = BedrockService()
        self.file_service = FileService()
        self.user_preferences_accessor = UserPreferencesAccessor()

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
            message = self._prepare_message(message_text.replace(f"<@{bot_user_id}>", "").strip(), files, app_client)
            model_response = self._get_model_response([message], user_id)
            say(model_response, thread_ts=ts)
        except Exception as e:
            logger.error(f"An error occurred while processing the app mention: {str(e)}")
            say(text=f"Error: {str(e)}", thread_ts=ts)

    def _handle_direct_message(self, message_text, ts, user_id, say, files, app_client):
        logger.info("Processing direct message")
        try:
            message = self._prepare_message(message_text, files, app_client)
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
                prepared_message = self._prepare_message(combined_text, all_files, app_client)
                prepared_message["role"] = "assistant" if is_assistant else "user"
                messages.append(prepared_message)

            model_response = self._get_model_response(messages, user_id)
            say(model_response, thread_ts=thread_ts)

        except Exception as e:
            logger.error(f"Error while processing threaded conversation: {str(e)}")
            say(text=f"Error: {str(e)}", thread_ts=thread_ts)

    def _prepare_message(self, text, files, app_client):
        """
        Prepares a message with text and any attached files.

        Args:
            text (str): The message text.
            files (list): List of file attachments from Slack.
            app_client: The Slack app client for authentication.

        Returns:
            dict: A formatted message for the model.
        """
        if not files:
            return {
                "role": "user",
                "content": [{"text": text}]
            }
        message = {
            "role": "user",
            "content": [{"text": text}]
        }

        headers = {
            "Authorization": f"Bearer {app_client.token}"
        }

        for file in files:
            try:
                file_content = self.file_service.download_file(
                    file["url_private_download"],
                    headers
                )
                file_message = self._prepare_message_with_file(text, file_content, file)
                # Append the file content to the existing message
                message["content"].extend(file_message["content"][1:])
            except Exception as e:
                logger.error(f"Error processing file {file['name']}: {e}")
                # Add error note to the existing text
                message["content"][0]["text"] += f" (Note: Failed to process attached file: {file['name']})"

        return message
            
    def _prepare_message_with_file(self, text, file_content, file_info):
        """
        Prepares a message with file content for the model.

        Args:
            text (str): The text message.
            file_content (bytes): The file content.
            file_info (dict): Information about the file including type and format.

        Returns:
            dict: A formatted message for the model.

        Raises:
            ValueError: If the file type is not supported.
        """
        message = {
            "role": "user",
            "content": [{"text": text}]
        }
        logger.info(f"Preparing message with file info: {file_info}")

        filetype = file_info["filetype"].lower()

        if filetype in self.SUPPORTED_IMAGE_TYPES:
            # Convert jpg to jpeg for model compatibility
            format_type = "jpeg" if filetype == "jpg" else filetype
            message["content"].append({
                "image": {
                    "format": format_type,
                    "source": {
                        "bytes": file_content
                    }
                }
            })
        elif filetype in self.SUPPORTED_VIDEO_TYPES:
            message["content"].append({
                "video": {
                    "format": filetype,
                    "source": {
                        "bytes": file_content
                    }
                }
            })
        elif filetype in self.SUPPORTED_DOCUMENT_TYPES:
            message["content"].append({
                "document": {
                    "name": "".join(c if c.isalnum() else "_" for c in file_info["name"]),
                    "format": filetype,
                    "source": {
                        "bytes": file_content
                    }
                }
            })
        else:
            raise ValueError(
                f"Unsupported file type: {filetype}. Supported types are: "
                f"images ({', '.join(self.SUPPORTED_IMAGE_TYPES)}), "
                f"videos ({', '.join(self.SUPPORTED_VIDEO_TYPES)}), and "
                f"documents ({', '.join(self.SUPPORTED_DOCUMENT_TYPES)})"
            )

        return message

    def _get_model_response(self, messages, user_id):
        user_model = self.user_preferences_accessor.get_user_model(user_id)
        return self.bedrock_service.invoke_model(messages, user_model) 