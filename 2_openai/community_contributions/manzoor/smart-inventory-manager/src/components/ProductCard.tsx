import React from 'react';
import { Product } from '../types';
interface Props { product: Product; }
const ProductCard: React.FC<Props> = ({ product }) => (
  <div style={{ border: '1px solid #ddd', padding: 12, borderRadius: 8 }}>
    <h3>{product.name}</h3>
    <p>SKU: {product.sku}</p>
    <p>Cost: ${product.priceCost}</p>
    <p>Sell: ${product.priceSelling}</p>
  </div>
);
export default ProductCard;