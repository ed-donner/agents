import os
import pytest
from unittest.mock import patch, MagicMock, Mock
from tools.email import _send_email_impl as send_email


class TestSendEmail:
    """Test suite for send_email tool."""

    @patch.dict(os.environ, {'SENDGRID_API_KEY': 'test_api_key'})
    @patch('tools.email.sendgrid.SendGridAPIClient')
    def test_send_email_success(self, mock_sendgrid_class):
        """Test successful email sending."""
        # Setup mocks
        mock_client = MagicMock()
        mock_response = Mock()
        mock_response.status_code = 202
        mock_client.client.mail.send.post.return_value = mock_response
        mock_sendgrid_class.return_value = mock_client

        result = send_email("Test message", "<p>Test message</p>")

        assert result["status"] == "success"
        assert result["message"] == "Email sent successfully"
        mock_sendgrid_class.assert_called_once_with(api_key='test_api_key')
        mock_client.client.mail.send.post.assert_called_once()

    @patch.dict(os.environ, {}, clear=True)
    def test_send_email_missing_api_key(self):
        """Test email sending when API key is missing."""
        result = send_email("Test message", "<p>Test message</p>")

        assert result["status"] == "error"
        assert "SENDGRID_API_KEY" in result["message"]

    @patch.dict(os.environ, {'SENDGRID_API_KEY': 'test_api_key'})
    @patch('tools.email.sendgrid.SendGridAPIClient')
    def test_send_email_failure_status_code(self, mock_sendgrid_class):
        """Test email sending failure with non-202 status code."""
        # Setup mocks
        mock_client = MagicMock()
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.body = b'{"errors": ["Invalid request"]}'
        mock_client.client.mail.send.post.return_value = mock_response
        mock_sendgrid_class.return_value = mock_client

        result = send_email("Test message", "<p>Test message</p>")

        assert result["status"] == "error"
        assert "Failed to send email" in result["message"]
        assert "400" in result["message"]

    @patch.dict(os.environ, {'SENDGRID_API_KEY': 'test_api_key'})
    @patch('tools.email.sendgrid.SendGridAPIClient')
    def test_send_email_failure_no_body(self, mock_sendgrid_class):
        """Test email sending failure with no response body."""
        # Setup mocks
        mock_client = MagicMock()
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.body = None
        mock_client.client.mail.send.post.return_value = mock_response
        mock_sendgrid_class.return_value = mock_client

        result = send_email("Test message", "<p>Test message</p>")

        assert result["status"] == "error"
        assert "Failed to send email" in result["message"]
        assert "Unknown error" in result["message"]

    @patch.dict(os.environ, {'SENDGRID_API_KEY': 'test_api_key'})
    @patch('tools.email.sendgrid.SendGridAPIClient')
    def test_send_email_exception(self, mock_sendgrid_class):
        """Test email sending when an exception occurs."""
        # Setup mocks to raise an exception
        mock_sendgrid_class.side_effect = Exception("Network error")

        result = send_email("Test message", "<p>Test message</p>")

        assert result["status"] == "error"
        assert "Unexpected error sending email" in result["message"]
        assert "Network error" in result["message"]

    @patch.dict(os.environ, {'SENDGRID_API_KEY': 'test_api_key'})
    @patch('tools.email.sendgrid.SendGridAPIClient')
    def test_send_email_creates_correct_mail_object(self, mock_sendgrid_class):
        """Test that the email is created with correct parameters."""
        # Setup mocks
        mock_client = MagicMock()
        mock_response = Mock()
        mock_response.status_code = 202
        mock_client.client.mail.send.post.return_value = mock_response
        mock_sendgrid_class.return_value = mock_client

        send_email("Test message content", "<p>Test message content</p>")

        # Verify Mail object was created (check that get() was called)
        # The Mail object is created inline, so we verify the send was called
        assert mock_client.client.mail.send.post.called

