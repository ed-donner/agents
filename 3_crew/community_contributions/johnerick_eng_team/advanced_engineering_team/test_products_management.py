
import unittest
from unittest.mock import Mock

class ProductManager:
    def __init__(self):
        self.products = {}
        self.next_product_id = 1
    
    def create_product(self, product_name: str, coverage_options: dict, premium_logic: callable, claim_computation_rate: float) -> dict:
        """
        Creates a new insurance product with the specified parameters.
        """
        product_id = self.next_product_id
        self.next_product_id += 1
        
        product = {
            'product_id': product_id,
            'product_name': product_name,
            'coverage_options': coverage_options,
            'premium_logic': premium_logic,
            'claim_computation_rate': claim_computation_rate
        }
        
        self.products[product_id] = product
        return product
    
    def update_product(self, product_id: int, updates: dict) -> bool:
        """
        Updates an existing insurance product with new details.
        """
        if product_id not in self.products:
            return False
        
        for key, value in updates.items():
            if key in self.products[product_id]:
                self.products[product_id][key] = value
        
        return True
    
    def delete_product(self, product_id: int) -> bool:
        """
        Deletes an insurance product by its ID.
        """
        if product_id in self.products:
            del self.products[product_id]
            return True
        return False
    
    def get_product(self, product_id: int) -> dict:
        """
        Retrieves full information about a specific product by ID.
        """
        return self.products.get(product_id, {})
    
    def list_products(self) -> list:
        """
        Lists all available insurance products.
        """
        return list(self.products.values())
    
    def define_claim_computation_rate(self, product_id: int, rate: float) -> bool:
        """
        Defines or updates the claim computation rate for a specific product.
        """
        if product_id not in self.products:
            return False
        
        self.products[product_id]['claim_computation_rate'] = rate
        return True
    
    def define_coverage_options(self, product_id: int, options: dict) -> bool:
        """
        Defines or updates coverage options for a specific product.
        """
        if product_id not in self.products:
            return False
        
        self.products[product_id]['coverage_options'] = options
        return True
    
    def define_premium_logic(self, product_id: int, logic: callable) -> bool:
        """
        Defines or updates the premium calculation logic for a specific product.
        """
        if product_id not in self.products:
            return False
        
        self.products[product_id]['premium_logic'] = logic
        return True
    
    def query_products(self, filter_criteria: dict) -> list:
        """
        Queries the list of insurance products based on given filter criteria.
        """
        filtered_products = []
        
        for product in self.products.values():
            match = True
            for key, value in filter_criteria.items():
                if key in product:
                    if product[key] != value:
                        match = False
                        break
                else:
                    match = False
                    break
            
            if match:
                filtered_products.append(product)
        
        return filtered_products


class TestProductManager(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.product_manager = ProductManager()
        self.sample_coverage_options = {
            'basic': 1000,
            'premium': 5000,
            'comprehensive': 10000
        }
        self.sample_premium_logic = lambda age, coverage: age * 10 + coverage * 0.1
        self.sample_claim_rate = 0.05
    
    def test_init(self):
        """Test ProductManager initialization."""
        pm = ProductManager()
        self.assertEqual(pm.products, {})
        self.assertEqual(pm.next_product_id, 1)
    
    def test_create_product_success(self):
        """Test successful product creation."""
        product = self.product_manager.create_product(
            product_name="Auto Insurance",
            coverage_options=self.sample_coverage_options,
            premium_logic=self.sample_premium_logic,
            claim_computation_rate=self.sample_claim_rate
        )
        
        self.assertEqual(product['product_id'], 1)
        self.assertEqual(product['product_name'], "Auto Insurance")
        self.assertEqual(product['coverage_options'], self.sample_coverage_options)
        self.assertEqual(product['premium_logic'], self.sample_premium_logic)
        self.assertEqual(product['claim_computation_rate'], self.sample_claim_rate)
        
        # Check that product is stored in products dictionary
        self.assertIn(1, self.product_manager.products)
        self.assertEqual(self.product_manager.next_product_id, 2)
    
    def test_create_multiple_products(self):
        """Test creating multiple products with incremental IDs."""
        product1 = self.product_manager.create_product(
            "Product 1", {}, lambda x: x, 0.1
        )
        product2 = self.product_manager.create_product(
            "Product 2", {}, lambda x: x, 0.2
        )
        
        self.assertEqual(product1['product_id'], 1)
        self.assertEqual(product2['product_id'], 2)
        self.assertEqual(self.product_manager.next_product_id, 3)
    
    def test_update_product_success(self):
        """Test successful product update."""
        # Create a product first
        product = self.product_manager.create_product(
            "Test Product", self.sample_coverage_options, 
            self.sample_premium_logic, self.sample_claim_rate
        )
        
        # Update the product
        new_coverage = {'basic': 2000, 'premium': 6000}
        new_rate = 0.08
        updates = {
            'coverage_options': new_coverage,
            'claim_computation_rate': new_rate
        }
        
        result = self.product_manager.update_product(1, updates)
        
        self.assertTrue(result)
        updated_product = self.product_manager.get_product(1)
        self.assertEqual(updated_product['coverage_options'], new_coverage)
        self.assertEqual(updated_product['claim_computation_rate'], new_rate)
    
    def test_update_product_nonexistent(self):
        """Test updating a non-existent product."""
        result = self.product_manager.update_product(999, {'product_name': 'New Name'})
        self.assertFalse(result)
    
    def test_update_product_invalid_key(self):
        """Test updating with invalid keys (should be ignored)."""
        product = self.product_manager.create_product(
            "Test Product", {}, lambda x: x, 0.1
        )
        
        result = self.product_manager.update_product(1, {
            'product_name': 'Updated Name',
            'invalid_key': 'should be ignored'
        })
        
        self.assertTrue(result)
        updated_product = self.product_manager.get_product(1)
        self.assertEqual(updated_product['product_name'], 'Updated Name')
        self.assertNotIn('invalid_key', updated_product)
    
    def test_delete_product_success(self):
        """Test successful product deletion."""
        product = self.product_manager.create_product(
            "Test Product", {}, lambda x: x, 0.1
        )
        
        result = self.product_manager.delete_product(1)
        
        self.assertTrue(result)
        self.assertNotIn(1, self.product_manager.products)
        self.assertEqual(self.product_manager.get_product(1), {})
    
    def test_delete_product_nonexistent(self):
        """Test deleting a non-existent product."""
        result = self.product_manager.delete_product(999)
        self.assertFalse(result)
    
    def test_get_product_success(self):
        """Test retrieving an existing product."""
        created_product = self.product_manager.create_product(
            "Test Product", self.sample_coverage_options, 
            self.sample_premium_logic, self.sample_claim_rate
        )
        
        retrieved_product = self.product_manager.get_product(1)
        
        self.assertEqual(retrieved_product, created_product)
    
    def test_get_product_nonexistent(self):
        """Test retrieving a non-existent product."""
        result = self.product_manager.get_product(999)
        self.assertEqual(result, {})
    
    def test_list_products_empty(self):
        """Test listing products when none exist."""
        result = self.product_manager.list_products()
        self.assertEqual(result, [])
    
    def test_list_products_with_data(self):
        """Test listing products when products exist."""
        product1 = self.product_manager.create_product(
            "Product 1", {}, lambda x: x, 0.1
        )
        product2 = self.product_manager.create_product(
            "Product 2", {}, lambda x: x, 0.2
        )
        
        result = self.product_manager.list_products()
        
        self.assertEqual(len(result), 2)
        self.assertIn(product1, result)
        self.assertIn(product2, result)
    
    def test_define_claim_computation_rate_success(self):
        """Test successfully defining claim computation rate."""
        product = self.product_manager.create_product(
            "Test Product", {}, lambda x: x, 0.1
        )
        
        result = self.product_manager.define_claim_computation_rate(1, 0.15)
        
        self.assertTrue(result)
        updated_product = self.product_manager.get_product(1)
        self.assertEqual(updated_product['claim_computation_rate'], 0.15)
    
    def test_define_claim_computation_rate_nonexistent(self):
        """Test defining claim computation rate for non-existent product."""
        result = self.product_manager.define_claim_computation_rate(999, 0.15)
        self.assertFalse(result)
    
    def test_define_coverage_options_success(self):
        """Test successfully defining coverage options."""
        product = self.product_manager.create_product(
            "Test Product", {}, lambda x: x, 0.1
        )
        
        new_options = {'new_basic': 3000, 'new_premium': 8000}
        result = self.product_manager.define_coverage_options(1, new_options)
        
        self.assertTrue(result)
        updated_product = self.product_manager.get_product(1)
        self.assertEqual(updated_product['coverage_options'], new_options)
    
    def test_define_coverage_options_nonexistent(self):
        """Test defining coverage options for non-existent product."""
        result = self.product_manager.define_coverage_options(999, {})
        self.assertFalse(result)
    
    def test_define_premium_logic_success(self):
        """Test successfully defining premium logic."""
        product = self.product_manager.create_product(
            "Test Product", {}, lambda x: x, 0.1
        )
        
        new_logic = lambda age, coverage: age * 5 + coverage * 0.05
        result = self.product_manager.define_premium_logic(1, new_logic)
        
        self.assertTrue(result)
        updated_product = self.product_manager.get_product(1)
        self.assertEqual(updated_product['premium_logic'], new_logic)
    
    def test_define_premium_logic_nonexistent(self):
        """Test defining premium logic for non-existent product."""
        result = self.product_manager.define_premium_logic(999, lambda x: x)
        self.assertFalse(result)
    
    def test_query_products_empty_filter(self):
        """Test querying products with empty filter criteria."""
        product1 = self.product_manager.create_product(
            "Product 1", {}, lambda x: x, 0.1
        )
        product2 = self.product_manager.create_product(
            "Product 2", {}, lambda x: x, 0.2
        )
        
        result = self.product_manager.query_products({})
        
        self.assertEqual(len(result), 2)
        self.assertIn(product1, result)
        self.assertIn(product2, result)
    
    def test_query_products_single_criterion(self):
        """Test querying products with single filter criterion."""
        product1 = self.product_manager.create_product(
            "Auto Insurance", {}, lambda x: x, 0.1
        )
        product2 = self.product_manager.create_product(
            "Health Insurance", {}, lambda x: x, 0.2
        )
        
        result = self.product_manager.query_products({'product_name': 'Auto Insurance'})
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], product1)
    
    def test_query_products_multiple_criteria(self):
        """Test querying products with multiple filter criteria."""
        product1 = self.product_manager.create_product(
            "Auto Insurance", {'basic': 1000}, lambda x: x, 0.1
        )
        product2 = self.product_manager.create_product(
            "Auto Insurance", {'basic': 2000}, lambda x: x, 0.1
        )
        product3 = self.product_manager.create_product(
            "Health Insurance", {'basic': 1000}, lambda x: x, 0.1
        )
        
        result = self.product_manager.query_products({
            'product_name': 'Auto Insurance',
            'claim_computation_rate': 0.1
        })
        
        self.assertEqual(len(result), 2)
        self.assertIn(product1, result)
        self.assertIn(product2, result)
        self.assertNotIn(product3, result)
    
    def test_query_products_no_matches(self):
        """Test querying products with no matching results."""
        product = self.product_manager.create_product(
            "Auto Insurance", {}, lambda x: x, 0.1
        )
        
        result = self.product_manager.query_products({'product_name': 'Health Insurance'})
        
        self.assertEqual(result, [])
    
    def test_query_products_nonexistent_key(self):
        """Test querying products with non-existent key."""
        product = self.product_manager.create_product(
            "Auto Insurance", {}, lambda x: x, 0.1
        )
        
        result = self.product_manager.query_products({'nonexistent_key': 'value'})
        
        self.assertEqual(result, [])


if __name__ == '__main__':
    unittest.main()
