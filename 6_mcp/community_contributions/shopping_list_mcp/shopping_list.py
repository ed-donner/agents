"""
shopping_list.py - Core business logic for shopping list management.

This is PURE PYTHON - no MCP here!
The MCP server will import and use this class.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional
import json

@dataclass
class ShoppingItem:
    """Represents a single item in the shopping list."""
    name: str
    quantity: int = 1
    category: str = "General"
    price: Optional[float] = None  # Price per unit (optional)
    added_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))

   
class ShoppingList:
    """
    Manages an in-memory shopping list with budget tracking.
    
    This is a regular Python class - the MCP server will wrap its methods as "tools".
    """

    def __init__(self):
        # Dictionary to store items (key = lowercase name, value = ShoppingItem)
        self._items: Dict[str, ShoppingItem] = {}
        # Budget limit
        self._budget: float = 100.0
    # ─────────────────────────────────────────────────────────────
    # CRUD Operations (Create, Read, Update, Delete)
    # ─────────────────────────────────────────────────────────────
    def add_item(self, name: str, quantity: int = 1, 
                 category: str = "General", price: float = None) -> dict:
        """
        Add an item to the shopping list.
        If item already exists, increases the quantity.
        
        Returns a dict with success status and message.
        """
        key = name.lower().strip()
        
        if key in self._items:
            # Item exists - update quantity
            self._items[key].quantity += quantity
            return {
                "success": True,
                "action": "updated",
                "message": f"Updated '{name}' - now have {self._items[key].quantity}",
                "item": self._item_to_dict(self._items[key])
            }
        else:
            # New item - add it
            self._items[key] = ShoppingItem(
                name=name.strip(),
                quantity=quantity,
                category=category,
                price=price
            )
            return {
                "success": True,
                "action": "added",
                "message": f"Added '{name}' to shopping list",
                "item": self._item_to_dict(self._items[key])
            }

    def remove_item(self, name: str) -> dict:
        """Remove an item from the shopping list."""
        key = name.lower().strip()
        
        if key in self._items:
            removed = self._items.pop(key)
            return {
                "success": True,
                "message": f"Removed '{removed.name}' from shopping list"
            }
        else:
            return {
                "success": False,
                "message": f"Item '{name}' not found in shopping list"
            }

    def get_list(self) -> dict:
        """Get all items in the shopping list."""
        items = [self._item_to_dict(item) for item in self._items.values()]
        total_cost = self.get_total_cost()
        
        return {
            "success": True,
            "items": items,
            "total_items": len(items),
            "total_cost": total_cost,
            "budget": self._budget,
            "remaining_budget": round(self._budget - total_cost, 2)
        }

    def clear_list(self) -> dict:
        """Clear all items from the shopping list."""
        count = len(self._items)
        self._items.clear()
        return {
            "success": True,
            "message": f"Cleared {count} items from shopping list"
        }
    # ─────────────────────────────────────────────────────────────
    # Budget Operations
    # ─────────────────────────────────────────────────────────────
    
    def set_budget(self, amount: float) -> dict:
        """Set the shopping budget."""
        self._budget = amount
        return {
            "success": True,
            "message": f"Budget set to ${amount:.2f}",
            "budget": self._budget
        }

    def get_total_cost(self) -> float:
        """Calculate total cost of items with prices."""
        total = 0.0
        for item in self._items.values():
            if item.price is not None:
                total += item.price * item.quantity
        return round(total, 2)
    def get_budget_status(self) -> dict:
        """Get budget status with visual indicator."""
        total = self.get_total_cost()
        remaining = self._budget - total
        percentage = (total / self._budget * 100) if self._budget > 0 else 0
        
        # Determine status emoji
        if percentage < 80:
            status = "🟢 On track!"
        elif percentage < 100:
            status = "🟡 Approaching budget limit"
        else:
            status = f"🔴 Over budget by ${abs(remaining):.2f}!"
        
        return {
            "success": True,
            "total_cost": total,
            "budget": self._budget,
            "remaining": round(remaining, 2),
            "percentage_used": round(percentage, 1),
            "status": status
        }

    # ─────────────────────────────────────────────────────────────
    # Helper Methods
    # ─────────────────────────────────────────────────────────────
    
    def _item_to_dict(self, item: ShoppingItem) -> dict:
        """Convert ShoppingItem to dictionary."""
        return {
            "name": item.name,
            "quantity": item.quantity,
            "category": item.category,
            "price": item.price,
            "added_at": item.added_at
        }
    
    # ─────────────────────────────────────────────────────────────
    # Sharing / Export Methods
    # ─────────────────────────────────────────────────────────────
    
    def format_for_sms(self) -> str:
        """Format shopping list for SMS (concise, no emojis)."""
        if not self._items:
            return "Shopping list is empty"
        
        lines = ["Shopping List:"]
        for item in self._items.values():
            price_str = f" ${item.price:.2f}" if item.price else ""
            lines.append(f"- {item.name} x{item.quantity}{price_str}")
        
        total = self.get_total_cost()
        if total > 0:
            lines.append(f"Total: ${total:.2f}")
        
        return "\n".join(lines)
    
    def format_for_email(self) -> str:
        """Format shopping list for email (detailed, with categories)."""
        if not self._items:
            return "Your shopping list is empty."
        
        # Group by category
        by_category: Dict[str, List[ShoppingItem]] = {}
        for item in self._items.values():
            cat = item.category
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(item)
        
        lines = ["🛒 Your Shopping List\n"]
        
        for category, items in sorted(by_category.items()):
            lines.append(f"\n📦 {category}:")
            for item in items:
                price_str = f" - ${item.price:.2f}" if item.price else ""
                lines.append(f"  • {item.name} (x{item.quantity}){price_str}")
        
        lines.append(f"\n{'─' * 30}")
        total = self.get_total_cost()
        lines.append(f"💰 Total: ${total:.2f}")
        lines.append(f"📊 Budget: ${self._budget:.2f}")
        lines.append(f"💵 Remaining: ${self._budget - total:.2f}")
        
        return "\n".join(lines)
# ─────────────────────────────────────────────────────────────────
# Singleton Pattern - One global shopping list instance
# ─────────────────────────────────────────────────────────────────

_shopping_list_instance = None

def get_shopping_list() -> ShoppingList:
    """
    Get the global shopping list instance.
    Creates one if it doesn't exist (singleton pattern).
    """
    global _shopping_list_instance
    if _shopping_list_instance is None:
        _shopping_list_instance = ShoppingList()
    return _shopping_list_instance

if __name__ == "__main__":
    print("🧪 Testing ShoppingList class directly (no MCP)\n")
    
    # Create a shopping list
    my_list = ShoppingList()
    
    # Test adding items
    print("Adding items...")
    print(my_list.add_item("Milk", quantity=2, category="Dairy", price=4.99))
    print(my_list.add_item("Bread", quantity=1, category="Bakery", price=3.50))
    print(my_list.add_item("Apples", quantity=6, category="Produce", price=0.75))
    
    # Test getting the list
    print("\n📋 Current list:")
    print(json.dumps(my_list.get_list(), indent=2))
    
    # Test budget
    print("\n💰 Setting budget to $25...")
    print(my_list.set_budget(25.0))
    
    print("\n📊 Budget status:")
    print(json.dumps(my_list.get_budget_status(), indent=2))
    
    # Test removing
    print("\n🗑️ Removing bread...")
    print(my_list.remove_item("Bread"))
    
    print("\n📋 Final list:")
    print(json.dumps(my_list.get_list(), indent=2))