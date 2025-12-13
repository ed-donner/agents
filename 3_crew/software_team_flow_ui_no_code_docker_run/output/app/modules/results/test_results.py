import unittest
from results import Results

class TestResults(unittest.TestCase):
    def setUp(self):
        self.results = Results()

    def test_add_result(self):
        self.results.add_result("Test Result 1")
        self.assertIn("Test Result 1", self.results.get_results())

    def test_get_results(self):
        self.results.add_result("Test Result 2")
        result = self.results.get_results()
        self.assertEqual(result, ["Test Result 2"])

    def test_clear_results(self):
        self.results.add_result("Test Result 3")
        self.results.clear_results()
        self.assertEqual(self.results.get_results(), [])

    def test_multiple_results(self):
        self.results.add_result("Test Result 4")
        self.results.add_result("Test Result 5")
        self.assertIn("Test Result 4", self.results.get_results())
        self.assertIn("Test Result 5", self.results.get_results())
        self.assertEqual(len(self.results.get_results()), 2)

    def test_clear_results_multiple(self):
        self.results.add_result("Test Result 6")
        self.results.add_result("Test Result 7")
        self.results.clear_results()
        self.assertEqual(self.results.get_results(), [])

if __name__ == '__main__':
    unittest.main()