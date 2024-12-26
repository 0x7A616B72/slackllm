import unittest
from unittest.mock import Mock, patch
from service.file_service import FileService

class TestFileService(unittest.TestCase):
    def setUp(self):
        self.service = FileService()
        self.mock_response = Mock()
        self.mock_response.content = b"test_content"

    @patch('requests.get')
    def test_download_file_success(self, mock_get):
        # Setup
        mock_get.return_value = self.mock_response

        # Execute
        result = self.service.download_file(
            "some_url",
            {"Authorization": "Bearer test-token"}
        )

        # Assert
        self.assertEqual(result, b"test_content")
        mock_get.assert_called_once_with(
            "some_url",
            headers={"Authorization": "Bearer test-token"}
        )

    @patch('requests.get')
    def test_download_file_error(self, mock_get):
        # Setup
        mock_get.side_effect = Exception("Download failed")

        # Execute and Assert
        with self.assertRaises(Exception):
            self.service.download_file(
                "some_url",
                {"Authorization": "Bearer test-token"}
            )

if __name__ == '__main__':
    unittest.main()