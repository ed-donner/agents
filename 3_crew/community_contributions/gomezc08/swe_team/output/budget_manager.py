import json
from datetime import datetime
from typing import List, Dict, Union

class BudgetTracker:
    def __init__(self):
        self.expenses: List[Dict[str, Union[float, str, datetime]]] = []

    def add_expense(self, amount: float, category: str, date: str) -> None:
        try:
            expense_date = datetime.strptime(date, '%Y-%m-%d')
            self.expenses.append({'amount': amount, 'category': category, 'date': expense_date})
        except ValueError:
            print("Error: Date must be in 'YYYY-MM-DD' format.")

    def calculate_total_spending(self) -> float:
        return sum(expense['amount'] for expense in self.expenses)

    def calculate_spending_by_category(self, category: str) -> float:
        return sum(expense['amount'] for expense in self.expenses if expense['category'] == category)

    def save_to_file(self, file_path: str) -> None:
        try:
            with open(file_path, 'w') as file:
                json.dump(self.expenses, file, default=str)
        except IOError:
            print("Error: Unable to save to file.")

    def load_from_file(self, file_path: str) -> None:
        try:
            with open(file_path, 'r') as file:
                self.expenses = json.load(file)
                for expense in self.expenses:
                    expense['date'] = datetime.strptime(expense['date'], '%Y-%m-%d')
        except IOError:
            print("Error: Unable to load from file.")
        except ValueError:
            print("Error: Invalid data format in the file.")

def main():
    tracker = BudgetTracker()
    tracker.add_expense(100.0, 'Food', '2023-10-01')
    tracker.add_expense(50.0, 'Transport', '2023-10-02')
    print("Total spending:", tracker.calculate_total_spending())
    print("Food spending:", tracker.calculate_spending_by_category('Food'))
    tracker.save_to_file('expenses.json')
    tracker.load_from_file('expenses.json')

if __name__ == "__main__":
    main()