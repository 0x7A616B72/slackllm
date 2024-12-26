import requests
from config import logger

class FileService:
    def download_file(self, file_url, headers):
        """
        Downloads a file from Slack.

        Args:
            file_url (str): The URL to download the file from.
            headers (dict): Headers for the request, including authentication.

        Returns:
            bytes: The file content.

        Raises:
            Exception: If there's an error downloading the file.
        """
        try:
            logger.info(f"Downloading file from {file_url} with headers {headers}")
            response = requests.get(file_url, headers=headers)
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.error(f"Error downloading file: {e}")
            raise 