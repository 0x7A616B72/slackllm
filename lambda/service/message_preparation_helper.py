from config import logger
from service.file_service import FileService

class MessagePreparationHelper:
    # Supported file types
    SUPPORTED_IMAGE_TYPES = ["png", "jpg", "jpeg", "gif", "webp"]
    SUPPORTED_VIDEO_TYPES = ["mov", "mkv", "mp4", "webm", "flv", "mpeg", "mpg", "wmv", "three_gp"]
    SUPPORTED_DOCUMENT_TYPES = ["pdf", "csv", "doc", "docx", "xls", "xlsx", "html", "txt", "md"]

    def __init__(self):
        self.file_service = FileService()

    def prepare_message(self, text, files, app_client):
        """
        Prepares a message with text and any attached files.

        Args:
            text (str): The message text.
            files (list): List of file attachments from Slack.
            app_client: The Slack app client for authentication.

        Returns:
            dict: A formatted message for the model.

        Raises:
            ValueError: If an unsupported file type is encountered.
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
            except ValueError:
                # Re-raise ValueError for unsupported file types
                raise
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