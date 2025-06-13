from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# Basic Model
class User(BaseModel):
    name: str
    age: int
    email: str  # Changed from EmailStr to str
    is_active: bool = True  # Default value
    created_at: datetime = Field(default_factory=datetime.now)
    tags: List[str] = []  # List with default empty value
    bio: Optional[str] = None  # Optional field

# Example usage
try:
    # Valid data
    user1 = User(
        name="John Doe",
        age=30,
        email="john@example.com",
        tags=["python", "developer"]
    )
    print("Valid user created:", user1.model_dump())

    # Invalid data - will raise validation error
    user2 = User(
        name="Jane Doe",
        age="not a number",  # This should be an integer
        email="invalid-email",  # This should be a valid email
        tags="not a list"  # This should be a list
    )
except Exception as e:
    print("\nValidation error:", str(e))

# Nested Models
class Address(BaseModel):
    street: str
    city: str
    country: str
    postal_code: str

class Employee(BaseModel):
    name: str
    age: int
    address: Address
    skills: List[str]

# Example with nested model
try:
    employee = Employee(
        name="Alice Smith",
        age=28,
        address={
            "street": "123 Main St",
            "city": "Boston",
            "country": "USA",
            "postal_code": "02108"
        },
        skills=["Python", "Data Analysis", "Machine Learning"]
    )
    print("\nEmployee created:", employee.model_dump())
except Exception as e:
    print("\nValidation error:", str(e))

# Model with custom validation
class Product(BaseModel):
    name: str
    price: float = Field(gt=0)  # Price must be greater than 0
    quantity: int = Field(ge=0)  # Quantity must be greater than or equal to 0

    def model_post_init(self, __context):
        # Custom validation after model initialization
        if self.price * self.quantity > 1000:
            raise ValueError("Total value cannot exceed 1000")

# Example with custom validation
try:
    product = Product(
        name="Laptop",
        price=1200.0,  # This will fail because price * quantity > 1000
        quantity=1
    )
except Exception as e:
    print("\nProduct validation error:", str(e)) 