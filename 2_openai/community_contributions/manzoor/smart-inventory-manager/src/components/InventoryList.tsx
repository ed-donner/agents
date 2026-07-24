import React from 'react';
import { InventoryItem, Product } from '../types';
interface Props { items: InventoryItem[]; products: Product[]; }
const InventoryList: React.FC<Props> = ({ items, products }) => {
  const map = new Map<number, Product>();
  products.forEach(p => map.set(p.id, p));
  return (
    <ul style={{ listStyle: 'none', padding: 0 }}>
      {items.map(it => { const p = map.get(it.productId); return (
        <li key={it.id} style={{ border: '1px solid #ddd', padding: 8, marginBottom: 8 }}>
          <strong>{p?.name ?? 'Unknown'}</strong> - Qty: {it.quantity}
        </li>
      ); })}
    </ul>
  );
};
export default InventoryList;