import React from 'react';
import InventoryList from '../components/InventoryList';
import { Product, InventoryItem } from '../types';

const InventoryPage: React.FC = () => {
  const products: Product[] = [
    { id: 1, name: 'Widget A', sku: 'WGT-A', priceCost: 5, priceSelling: 10 },
    { id: 2, name: 'Widget B', sku: 'WGT-B', priceCost: 6, priceSelling: 12 }
  ];
  const inventory: InventoryItem[] = [
    { id: 1, productId: 1, warehouseId: 1, quantity: 120 },
    { id: 2, productId: 2, warehouseId: 1, quantity: 50 }
  ];
  return (
    <div>
      <h1>Inventory</h1>
      <InventoryList items={inventory} products={products} />
    </div>
  );
};
export default InventoryPage;