import pytest
from budget_manager import BudgetTracker

def test_add_expense_happy_path():
    tracker = BudgetTracker()
    tracker.add_expense(100.0, 'Food', '2023-10-01')
    assert len(tracker.expenses) == 1
    assert tracker.expenses[0]['amount'] == 100.0
    assert tracker.expenses[0]['category'] == 'Food'
    assert tracker.expenses[0]['date'].strftime('%Y-%m-%d') == '2023-10-01'

def test_add_expense_edge_case_invalid_date():
    tracker = BudgetTracker()
    tracker.add_expense(50.0, 'Transport', '2023/10/02')
    assert len(tracker.expenses) == 0

def test_calculate_total_spending_happy_path():
    tracker = BudgetTracker()
    tracker.add_expense(100.0, 'Food', '2023-10-01')
    tracker.add_expense(50.0, 'Transport', '2023-10-02')
    assert tracker.calculate_total_spending() == 150.0

def test_calculate_spending_by_category_happy_path():
    tracker = BudgetTracker()
    tracker.add_expense(100.0, 'Food', '2023-10-01')
    tracker.add_expense(50.0, 'Transport', '2023-10-02')
    assert tracker.calculate_spending_by_category('Food') == 100.0

def test_calculate_spending_by_category_edge_case_no_expenses():
    tracker = BudgetTracker()
    assert tracker.calculate_spending_by_category('Food') == 0.0

def test_save_to_file_happy_path(tmp_path):
    tracker = BudgetTracker()
    tracker.add_expense(100.0, 'Food', '2023-10-01')
    file_path = tmp_path / "test_expenses.json"
    tracker.save_to_file(file_path)
    
    with open(file_path, 'r') as file:
        data = json.load(file)
    assert len(data) == 1
    assert data[0]['amount'] == 100.0

def test_load_from_file_happy_path(tmp_path):
    tracker = BudgetTracker()
    file_path = tmp_path / "test_expenses.json"
    with open(file_path, 'w') as file:
        json.dump([{'amount': 100.0, 'category': 'Food', 'date': '2023-10-01'}], file)
    
    tracker.load_from_file(file_path)
    assert len(tracker.expenses) == 1
    assert tracker.expenses[0]['amount'] == 100.0

def test_load_from_file_edge_case_invalid_json(tmp_path):
    tracker = BudgetTracker()
    file_path = tmp_path / "invalid_expenses.json"
    with open(file_path, 'w') as file:
        file.write("this is not a json")
    
    tracker.load_from_file(file_path)
    assert len(tracker.expenses) == 0