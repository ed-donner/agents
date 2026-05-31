import unittest

from output.UserManagement import AuthenticationManager


class TestUserManagement(unittest.TestCase):
    def setUp(self):
        self.manager = AuthenticationManager()

    def test_register_and_get_user(self):
        success, user_id = self.manager.register("alice", "alice@example.com", "secret")
        self.assertTrue(success)
        user = self.manager.get_user(user_id)
        self.assertEqual(user.username, "alice")
        self.assertEqual(user.email, "alice@example.com")

    def test_duplicate_user_is_rejected(self):
        self.manager.register("alice", "alice@example.com", "secret")
        success, message = self.manager.register("alice", "other@example.com", "secret")
        self.assertFalse(success)
        self.assertEqual(message, "Username already exists")

    def test_authenticate_creates_session(self):
        self.manager.register("alice", "alice@example.com", "secret")
        success, payload = self.manager.authenticate("alice", "secret")
        self.assertTrue(success)
        self.assertIn("session_id", payload)
        self.assertIn("user_id", payload)


if __name__ == "__main__":
    unittest.main()
