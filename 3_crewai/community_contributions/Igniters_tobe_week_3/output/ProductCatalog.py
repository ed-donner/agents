from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4


@dataclass
class Category:
    name: str
    description: str
    category_id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        return {
            "category_id": self.category_id,
            "name": self.name,
            "description": self.description,
        }


@dataclass
class Product:
    name: str
    description: str
    price: float
    category_id: str
    stock: int = 0
    image_url: str | None = None
    product_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now(UTC)

    def to_dict(self):
        return {
            "product_id": self.product_id,
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "category_id": self.category_id,
            "stock": self.stock,
            "image_url": self.image_url,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class ProductCatalog:
    def __init__(self):
        self.categories = {}
        self.products = {}
        self.category_products = {}
        self._seed()

    def _seed(self):
        electronics = self.add_category("Electronics", "Devices and accessories")
        books = self.add_category("Books", "Print and digital books")
        home = self.add_category("Home", "Home essentials")
        self.add_product("Wireless Mouse", "Ergonomic mouse", 25.0, electronics, stock=25)
        self.add_product("Mechanical Keyboard", "Compact keyboard", 85.0, electronics, stock=15)
        self.add_product("Python Handbook", "Programming guide", 30.0, books, stock=20)
        self.add_product("Desk Lamp", "Adjustable lamp", 40.0, home, stock=12)

    def add_category(self, name, description):
        category = Category(name=name, description=description)
        self.categories[category.category_id] = category
        self.category_products[category.category_id] = []
        return category.category_id

    def add_product(self, name, description, price, category_id, stock=0, image_url=None):
        if category_id not in self.categories:
            return False, "Category does not exist"
        product = Product(
            name=name,
            description=description,
            price=float(price),
            category_id=category_id,
            stock=int(stock),
            image_url=image_url,
        )
        self.products[product.product_id] = product
        self.category_products.setdefault(category_id, []).append(product.product_id)
        return True, product.product_id

    def remove_product(self, product_id):
        product = self.products.get(product_id)
        if not product:
            return False, "Product not found"
        self.category_products[product.category_id] = [
            current_id
            for current_id in self.category_products.get(product.category_id, [])
            if current_id != product_id
        ]
        del self.products[product_id]
        return True, "Product removed"

    def get_product(self, product_id):
        return self.products.get(product_id)

    def list_products(self):
        return [product.to_dict() for product in self.products.values()]

    def get_all_categories(self):
        return [category.to_dict() for category in self.categories.values()]

    def get_products_by_category(self, category_id):
        product_ids = self.category_products.get(category_id, [])
        return [self.products[product_id].to_dict() for product_id in product_ids if product_id in self.products]

    def search_products(self, query="", category_id=None, min_price=None, max_price=None):
        needle = query.strip().lower()
        matches = []
        for product in self.products.values():
            if category_id and product.category_id != category_id:
                continue
            if min_price is not None and product.price < float(min_price):
                continue
            if max_price is not None and product.price > float(max_price):
                continue
            haystack = f"{product.name} {product.description}".lower()
            if needle and needle not in haystack:
                continue
            matches.append(product.to_dict())
        return matches

    def set_stock(self, product_id, stock):
        product = self.get_product(product_id)
        if not product:
            return False, "Product not found"
        product.update(stock=max(0, int(stock)))
        return True, product.stock

    def adjust_stock(self, product_id, delta):
        product = self.get_product(product_id)
        if not product:
            return False, "Product not found"
        new_stock = product.stock + int(delta)
        if new_stock < 0:
            return False, "Insufficient stock"
        product.update(stock=new_stock)
        return True, product.stock


product_catalog = ProductCatalog()


def add_product(name, description, price, category_id, stock=0, image_url=None):
    return product_catalog.add_product(name, description, price, category_id, stock, image_url)


def remove_product(product_id):
    return product_catalog.remove_product(product_id)


def get_product(product_id):
    product = product_catalog.get_product(product_id)
    return product.to_dict() if product else None


def list_products():
    return product_catalog.list_products()


def get_all_categories():
    return product_catalog.get_all_categories()


def get_products_by_category(category_id):
    return product_catalog.get_products_by_category(category_id)


def search_products(query="", category_id=None, min_price=None, max_price=None):
    return product_catalog.search_products(query, category_id, min_price, max_price)
