"""Unit tests for notifications; HTTP calls and configuration are simulated."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import tools


class RecordUserDetailsTests(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.emails_path = Path(directory.name) / "data" / "emails.txt"
        self.legacy_path = Path(directory.name) / "legacy_emails.txt"
        config = patch.multiple(
            tools, CHANNEL_TOKEN="test-token", DESTINATION="15555550100",
            RECORD_USER_DETAIL="test-contact-template",
            EMAILS_PATH=self.emails_path, LEGACY_EMAILS_PATH=self.legacy_path,
        )
        config.start()
        self.addCleanup(config.stop)
        post = patch.object(tools.requests, "post")
        self.post = post.start()
        self.post.return_value.json.return_value = True
        self.addCleanup(post.stop)

    def test_sends_contact_fields_to_configured_template(self):
        result = tools.record_user_details(
            email="twin-test@example.com", name="Twin Test", notes="Integration test",
        )
        self.assertEqual(result, "OK")
        self.post.assert_called_once_with(
            tools.channel_url,
            json={
                "token": "test-token",
                "user_id": "whatsapp:15555550100",
                "conversation_id": "LupaiKanban",
                "message": "--template:test-contact-template",
                "params": ["Twin Test", "twin-test@example.com", "Integration test"],
            },
            timeout=20,
        )
        self.post.return_value.raise_for_status.assert_called_once_with()

    def test_optional_fields_have_defaults(self):
        tools.record_user_details("twin-test@example.com")
        self.assertEqual(self.post.call_args.kwargs["json"]["params"], [
            "Name not provided", "twin-test@example.com", "not provided",
        ])

    def test_http_error_is_not_reported_as_success(self):
        self.post.return_value.raise_for_status.side_effect = requests.HTTPError("Rejected")
        with self.assertRaises(requests.HTTPError):
            tools.record_user_details("twin-test@example.com")

    def test_timeout_is_not_reported_as_success(self):
        self.post.side_effect = requests.Timeout("Timed out")
        with self.assertRaises(requests.Timeout):
            tools.record_user_details("twin-test@example.com")

    def test_http_200_with_rejected_notification_is_not_success(self):
        self.post.return_value.json.return_value = False
        with self.assertRaisesRegex(RuntimeError, "did not confirm acceptance"):
            tools.record_user_details("twin-test@example.com")

    def test_non_json_response_is_not_reported_as_success(self):
        self.post.return_value.json.side_effect = ValueError("Not JSON")
        with self.assertRaises(ValueError):
            tools.record_user_details("twin-test@example.com")

    def test_duplicate_ignores_case_and_whitespace_and_sends_only_once(self):
        self.assertEqual(tools.record_user_details("Twin-Test@Example.com"), "OK")
        self.assertEqual(tools.record_user_details(" twin-test@EXAMPLE.com "), "Email already exists")
        self.post.assert_called_once()
        self.assertEqual(self.emails_path.read_text(), "twin-test@example.com\n")
        self.assertEqual(self.post.call_args.kwargs["json"]["params"][1], "Twin-Test@Example.com")

    def test_existing_file_is_checked_on_each_invocation(self):
        self.emails_path.parent.mkdir()
        self.emails_path.write_text(" TWIN-TEST@Example.com \n\n")
        self.assertEqual(tools.record_user_details("twin-test@example.com"), "Email already exists")
        self.post.assert_not_called()

    def test_lab3_list_is_respected_without_modifying_it(self):
        contents = " Twin-Test@Example.com \n"
        self.legacy_path.write_text(contents)
        self.assertEqual(tools.record_user_details("twin-test@example.com"), "Email already exists")
        self.post.assert_not_called()
        self.assertEqual(self.legacy_path.read_text(), contents)
        self.assertFalse(self.emails_path.exists())

    def test_failed_send_is_not_saved_and_can_be_retried(self):
        self.post.return_value.raise_for_status.side_effect = requests.HTTPError("Rejected")
        with self.assertRaises(requests.HTTPError):
            tools.record_user_details("twin-test@example.com")
        self.assertEqual(self.emails_path.read_text(), "")
        self.post.return_value.raise_for_status.side_effect = None
        self.assertEqual(tools.record_user_details("twin-test@example.com"), "OK")
        self.assertEqual(self.emails_path.read_text(), "twin-test@example.com\n")
        self.assertEqual(self.post.call_count, 2)

    def test_concurrent_sessions_only_send_once(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(tools.record_user_details, ["twin-test@example.com"] * 2))
        self.assertEqual(sorted(results), ["Email already exists", "OK"])
        self.post.assert_called_once()
        self.assertEqual(self.emails_path.read_text(), "twin-test@example.com\n")

    def test_empty_email_is_not_sent_or_saved(self):
        with self.assertRaises(ValueError):
            tools.record_user_details("   ")
        self.post.assert_not_called()
        self.assertFalse(self.emails_path.exists())


if __name__ == "__main__":
    unittest.main()
