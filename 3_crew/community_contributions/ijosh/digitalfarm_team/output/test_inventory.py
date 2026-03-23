import unittest
import tempfile
import os
import sqlite3
from inventory import InventoryManager


class TestInventoryManager(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.manager = InventoryManager(db_path=self.db_path)
        
    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)
        
    def test_add_crop(self):
        self.manager.add_crop('2023-07-01', 'Field D', 4000.0, 'Rice, new batch.')
        crops = self.manager.get_crops()
        self.assertEqual(len(crops), 4)
        self.assertEqual(crops[-1]['field_assignment'], 'Field D')
        
    def test_update_crop(self):
        self.manager.update_crop(1, harvest_date='2023-10-01', growth_stage='Mature', health_status='healthy', actual_yield=4500.0)
        crops = self.manager.get_crops()
        crop = next((crop for crop in crops if crop['id'] == 1), None)
        self.assertIsNotNone(crop)
        self.assertEqual(crop['growth_stage'], 'Mature')
        self.assertEqual(crop['actual_yield'], 4500.0)

    def test_register_livestock(self):
        self.manager.register_livestock('Sheep', 'West African Dwarf', '2021-05-20', 60.0, 'Pasture 3')
        livestock = self.manager.get_livestock()
        self.assertEqual(len(livestock), 4)
        self.assertEqual(livestock[-1]['species'], 'Sheep')
        
    def test_update_livestock(self):
        self.manager.update_livestock(1, weight=460.5, health_status='at-risk')
        livestock = self.manager.get_livestock()
        animal = next((animal for animal in livestock if animal['id'] == 1), None)
        self.assertIsNotNone(animal)
        self.assertEqual(animal['weight'], 460.5)
        self.assertEqual(animal['health_status'], 'at-risk')

    def test_add_inventory_item(self):
        self.manager.add_inventory_item('Tractor', 'pcs', 2000000.00, 'Machinery Co.', 5.0, 2.0)
        items = self.manager.get_inventory_items()
        self.assertEqual(len(items), 4)
        self.assertEqual(items[-1]['item_name'], 'Tractor')

    def test_update_inventory_item(self):
        self.manager.update_inventory_item(1, -30.0, 'use')
        items = self.manager.get_inventory_items()
        item = next((item for item in items if item['id'] == 1), None)
        self.assertIsNotNone(item)
        self.assertEqual(item['quantity'], 20.0)

    def test_get_transactions(self):
        self.manager.update_inventory_item(1, -30.0, 'use')
        transactions = self.manager.get_transactions()
        self.assertGreaterEqual(len(transactions), 4)  # Assuming initial 3 transactions
        self.assertEqual(transactions[0]['transaction_type'], 'use/disposal')
        
    def test_generate_report(self):
        report = self.manager.generate_report('2023-01-01', '2023-12-31', 'crop performance')
        self.assertGreaterEqual(len(report['data']), 1)
        self.assertEqual(report['report_type'], 'crop performance')


if __name__ == '__main__':
    unittest.main()