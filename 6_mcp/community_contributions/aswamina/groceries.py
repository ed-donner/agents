from pydantic import BaseModel, Field
from enum import Enum
import logging
import json
from dotenv import load_dotenv
from datetime import datetime
from typing import List, Optional
from database import write_grocery_inventory, write_grocery_consumption, write_log, read_grocery
from push import push

load_dotenv(override=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TransactionType(str, Enum):
    STOCKED = "Stocked"
    CONSUMED = "Consumed"


class Transaction(BaseModel):
    name: str
    quantity: int
    timestamp: str
    rationale: TransactionType

    def to_str(self) -> str:
        return f"{self.rationale.value}: {self.quantity} of {self.name} at {self.timestamp}."


class Grocery(BaseModel):
    name: str
    available_quantity: int = 0
    added_at: Optional[datetime] = None
    consumed_at: Optional[datetime] = None
    consumed_quantity: int = 0
    transactions: List[Transaction] = Field(default_factory=list)

    @classmethod
    def get(cls, name: str) -> Optional["Grocery"]:
        """Fetch an existing grocery by name. Returns None if not found."""
        fields = read_grocery(name.lower())
        if not fields:
            return None
        return cls(**fields)


    @classmethod
    def get_or_create(cls, name: str) -> "Grocery":
        """Fetch a grocery by name, creating it in the database if it doesn't exist."""
        fields = read_grocery(name.lower())
        if not fields:
            fields = {
                "name": name.lower(),
                "available_quantity": 0,
                "added_at": None,
                "consumed_at": None,
                "consumed_quantity": 0,
            }
            write_grocery_inventory(name.lower(), 0)
        return cls(**fields)


    def save(self, rationale: TransactionType):
        """Persist the current state to the database."""
        if rationale == TransactionType.STOCKED:
            write_grocery_inventory(self.name, self.available_quantity)
        elif rationale == TransactionType.CONSUMED:
            write_grocery_consumption(self.name, self.consumed_quantity)
        else:
            raise ValueError(f"Unrecognized transaction type: {rationale}")


    def stock(self, quantity: int):
        """Stock up on groceries."""
        if quantity <= 0:
            raise ValueError("Grocery quantity must be positive.")
        self.available_quantity += quantity
        self.added_at = datetime.now()
        logger.info(f"Stocked up on {quantity} of {self.name}. New quantity: {self.available_quantity}")
        write_log(name=self.name, type="grocery", message="Stocked grocery item")

        transaction = Transaction(
            name=self.name,
            quantity=quantity,
            timestamp=self.added_at.strftime("%Y-%m-%d %H:%M:%S"),
            rationale=TransactionType.STOCKED
        )
        self.transactions.append(transaction)
        self.save(TransactionType.STOCKED)


    def consume(self, quantity: int):
        """Update consumption of groceries."""
        if quantity <= 0:
            raise ValueError("Consumed quantity must be positive.")
        if quantity > self.available_quantity:
            raise ValueError(f"You cannot consume more than {self.available_quantity}")
        self.available_quantity -= quantity
        self.consumed_at = datetime.now()
        self.consumed_quantity += quantity
        logger.info(f"Consumed {quantity} of {self.name}.")
        write_log(name=self.name, type="grocery", message="Consumed grocery item")

        transaction = Transaction(
            name=self.name,
            quantity=quantity,
            timestamp=self.consumed_at.strftime("%Y-%m-%d %H:%M:%S"),
            rationale=TransactionType.CONSUMED
        )
        self.transactions.append(transaction)
        self.save(TransactionType.CONSUMED)

        if (self.available_quantity == 0):
            push(f"You have run out of {self.name}.  Please reorder at this time")


    def list_transactions(self) -> List[dict]:
        """List all transactions."""
        return [transaction.model_dump() for transaction in self.transactions]

    
    def get_grocery_report(self) -> str:
        """Return a JSON string representing the inventory of all groceries."""
        logger.info("Fetched grocery inventory report.")
        data = self.model_dump()
        json_string = json.dumps(data, default=str)
        return json_string


# Example usage:
if __name__ == "__main__":
    grocery = Grocery.get_or_create("eggs")
    grocery.stock(10)
    print(Grocery.get("eggs"))
    print(f"Transactions: {grocery.list_transactions()}")
