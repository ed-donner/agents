import unittest
from input import Input
from unittest.mock import patch

class TestInput(unittest.TestCase):

    @patch('builtins.input', side_effect=["test input"])
    def test_get_input(self, mock_input):
        user_input = Input("Enter something: ")
        result = user_input.get_input()
        self.assertEqual(result, "test input")
        self.assertEqual(user_input.get_value(), "test input")

    def test_validate_input_valid(self):
        user_input = Input("Enter something: ")
        user_input.value = "valid input"
        condition = lambda x: x == "valid input"
        self.assertTrue(user_input.validate_input(condition))

    def test_validate_input_invalid(self):
        user_input = Input("Enter something: ")
        user_input.value = "invalid input"
        condition = lambda x: x == "valid input"
        self.assertFalse(user_input.validate_input(condition))

    def test_get_value(self):
        user_input = Input("Enter something: ")
        user_input.value = "some value"
        self.assertEqual(user_input.get_value(), "some value")

if __name__ == '__main__':
    unittest.main()