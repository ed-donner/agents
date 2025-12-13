import unittest
from dashboard import Dashboard

class TestDashboard(unittest.TestCase):

    def setUp(self):
        self.dashboard = Dashboard()

    def test_initialization(self):
        self.assertIsInstance(self.dashboard, Dashboard)
    
    def test_add_widget(self):
        widget = {"type": "chart", "data": [1, 2, 3]}
        self.dashboard.add_widget(widget)
        self.assertIn(widget, self.dashboard.widgets)

    def test_remove_widget(self):
        widget = {"type": "chart", "data": [1, 2, 3]}
        self.dashboard.add_widget(widget)
        self.dashboard.remove_widget(widget)
        self.assertNotIn(widget, self.dashboard.widgets)
    
    def test_get_widgets(self):
        widget1 = {"type": "chart", "data": [1, 2, 3]}
        widget2 = {"type": "table", "data": [[1, 2], [3, 4]]}
        self.dashboard.add_widget(widget1)
        self.dashboard.add_widget(widget2)
        widgets = self.dashboard.get_widgets()
        self.assertEqual(len(widgets), 2)
        self.assertIn(widget1, widgets)
        self.assertIn(widget2, widgets)

    def test_update_widget(self):
        widget = {"type": "chart", "data": [1, 2, 3]}
        self.dashboard.add_widget(widget)
        updated_widget = {"type": "chart", "data": [4, 5, 6]}
        self.dashboard.update_widget(widget, updated_widget)
        self.assertIn(updated_widget, self.dashboard.widgets)
        self.assertNotIn(widget, self.dashboard.widgets)

    def test_clear_widgets(self):
        widget = {"type": "chart", "data": [1, 2, 3]}
        self.dashboard.add_widget(widget)
        self.dashboard.clear_widgets()
        self.assertEqual(len(self.dashboard.widgets), 0)

if __name__ == '__main__':
    unittest.main()