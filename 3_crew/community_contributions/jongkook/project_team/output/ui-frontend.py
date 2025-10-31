import gradio as gr
from typing import Dict, List, Any

# Simulated backend placeholders (to be replaced with actual backend integration)
class Backend:
    users = {}
    portfolios = {}
    transactions = {}
    
    @staticmethod
    def create_user(username: str, email: str, password: str) -> Dict[str, Any]:
        if username in Backend.users:
            return {"success": False, "message": "Username already exists."}
        Backend.users[username] = {"email": email, "password": password}
        Backend.portfolios[username] = {"cash": 10000.0, "stocks": {}}  # starting cash
        Backend.transactions[username] = []
        return {"success": True, "message": "User created successfully."}

    @staticmethod
    def update_user(username: str, email: str = None, password: str = None) -> Dict[str, Any]:
        if username not in Backend.users:
            return {"success": False, "message": "User does not exist."}
        if email:
            Backend.users[username]["email"] = email
        if password:
            Backend.users[username]["password"] = password
        return {"success": True, "message": "User updated successfully."}

    @staticmethod
    def verify_user(username: str, password: str) -> bool:
        return Backend.users.get(username, {}).get("password") == password

    @staticmethod
    def get_portfolio(username: str) -> Dict[str, Any]:
        return Backend.portfolios.get(username, {"cash": 0, "stocks": {}})

    @staticmethod
    def get_transaction_history(username: str) -> List[Dict[str, Any]]:
        return Backend.transactions.get(username, [])

    @staticmethod
    def buy_shares(username: str, ticker: str, quantity: int, price: float) -> Dict[str, Any]:
        if username not in Backend.portfolios:
            return {"success": False, "message": "User not found."}
        portfolio = Backend.portfolios[username]
        total_cost = price * quantity
        if portfolio["cash"] < total_cost:
            return {"success": False, "message": "Insufficient cash balance."}
        portfolio["cash"] -= total_cost
        portfolio["stocks"][ticker] = portfolio["stocks"].get(ticker, 0) + quantity
        Backend.transactions[username].append({"type": "buy", "ticker": ticker, "quantity": quantity, "price": price})
        return {"success": True, "message": "Shares bought successfully."}

    @staticmethod
    def sell_shares(username: str, ticker: str, quantity: int, price: float) -> Dict[str, Any]:
        if username not in Backend.portfolios:
            return {"success": False, "message": "User not found."}
        portfolio = Backend.portfolios[username]
        owned_quantity = portfolio["stocks"].get(ticker, 0)
        if owned_quantity < quantity:
            return {"success": False, "message": "Not enough shares to sell."}
        portfolio["stocks"][ticker] -= quantity
        if portfolio["stocks"][ticker] == 0:
            del portfolio["stocks"][ticker]
        total_gain = price * quantity
        portfolio["cash"] += total_gain
        Backend.transactions[username].append({"type": "sell", "ticker": ticker, "quantity": quantity, "price": price})
        return {"success": True, "message": "Shares sold successfully."}

# UI functions

current_user = {"username": None}  # simple session management

# User Account Management

def register_user(username, email, password, password_confirm):
    if password != password_confirm:
        return "Passwords do not match."
    result = Backend.create_user(username, email, password)
    if result["success"]:
        current_user["username"] = username
        return f"Registration successful. Welcome, {username}!"
    else:
        return result["message"]


def login_user(username, password):
    if Backend.verify_user(username, password):
        current_user["username"] = username
        return f"Login successful. Welcome back, {username}!"
    else:
        return "Invalid username or password."


def update_profile(email, password, password_confirm):
    if current_user["username"] is None:
        return "No user logged in."
    if password and password != password_confirm:
        return "Passwords do not match."
    result = Backend.update_user(current_user["username"], email=email if email else None, password=password if password else None)
    return result["message"]


# Portfolio Overview

def get_portfolio_overview():
    username = current_user["username"]
    if username is None:
        return "No user logged in.", "", ""
    portfolio = Backend.get_portfolio(username)
    cash_balance = portfolio["cash"]
    stocks = portfolio["stocks"]
    stocks_str = "" if not stocks else "\n".join([f"{ticker}: {qty} shares" for ticker, qty in stocks.items()])
    return f"Cash Balance: ${cash_balance:.2f}", stocks_str, ""


# Transaction History

def get_transaction_history():
    username = current_user["username"]
    if username is None:
        return "No user logged in.", []
    transactions = Backend.get_transaction_history(username)
    if not transactions:
        return "No transaction history available.", []
    history_list = []
    for t in transactions:
        t_type = t["type"].capitalize()
        history_list.append(f"{t_type}: {t['quantity']} shares of {t['ticker']} @ ${t['price']:.2f}")
    return "Transaction History:", history_list


# Transaction Execution

def execute_transaction(action, ticker, quantity, price):
    username = current_user["username"]
    if username is None:
        return "No user logged in."
    if quantity <= 0 or price <= 0:
        return "Quantity and price must be positive numbers."
    if action == "Buy":
        result = Backend.buy_shares(username, ticker.upper(), quantity, price)
    elif action == "Sell":
        result = Backend.sell_shares(username, ticker.upper(), quantity, price)
    else:
        return "Invalid transaction action."
    return result["message"]


# Build Gradio Interface

def build_ui():
    with gr.Blocks() as demo:
        gr.Markdown("# Trading Simulation Platform")

        with gr.Tab("User Account Management"):
            with gr.Row():
                with gr.Column():
                    gr.Markdown("## Register")
                    reg_username = gr.Textbox(label="Username", interactive=True)
                    reg_email = gr.Textbox(label="Email", interactive=True)
                    reg_password = gr.Textbox(label="Password", type="password", interactive=True)
                    reg_password_confirm = gr.Textbox(label="Confirm Password", type="password", interactive=True)
                    reg_button = gr.Button("Register")
                    reg_output = gr.Textbox(label="Status", interactive=False)

                    reg_button.click(fn=register_user, inputs=[reg_username, reg_email, reg_password, reg_password_confirm], outputs=reg_output)

                with gr.Column():
                    gr.Markdown("## Login")
                    login_username = gr.Textbox(label="Username", interactive=True)
                    login_password = gr.Textbox(label="Password", type="password", interactive=True)
                    login_button = gr.Button("Login")
                    login_output = gr.Textbox(label="Status", interactive=False)

                    login_button.click(fn=login_user, inputs=[login_username, login_password], outputs=login_output)

            with gr.Row():
                gr.Markdown("## Update Profile")
                upd_email = gr.Textbox(label="New Email (optional)", interactive=True)
                upd_password = gr.Textbox(label="New Password (optional)", type="password", interactive=True)
                upd_password_confirm = gr.Textbox(label="Confirm New Password", type="password", interactive=True)
                upd_button = gr.Button("Update Profile")
                upd_output = gr.Textbox(label="Status", interactive=False)

                upd_button.click(fn=update_profile, inputs=[upd_email, upd_password, upd_password_confirm], outputs=upd_output)

        with gr.Tab("Portfolio Overview"):
            cash_display = gr.Textbox(label="Cash Balance", interactive=False)
            stocks_display = gr.Textbox(label="Stock Holdings", interactive=False, lines=5)
            refresh_button = gr.Button("Refresh Portfolio")
            refresh_button.click(fn=get_portfolio_overview, inputs=None, outputs=[cash_display, stocks_display, gr.Textbox()])

        with gr.Tab("Transaction History"):
            trans_header = gr.Textbox(label="History Status", interactive=False)
            trans_list = gr.Textbox(label="Transactions", interactive=False, lines=10)
            history_button = gr.Button("Load History")
            history_button.click(fn=get_transaction_history, inputs=None, outputs=[trans_header, trans_list])

        with gr.Tab("Transaction Execution"):
            action_dropdown = gr.Dropdown(label="Action", choices=["Buy", "Sell"], value="Buy")
            ticker_input = gr.Textbox(label="Ticker Symbol", interactive=True)
            quantity_input = gr.Number(label="Quantity", precision=0)
            price_input = gr.Number(label="Price per Share", precision=2)
            execute_button = gr.Button("Execute Transaction")
            execute_output = gr.Textbox(label="Status", interactive=False)

            execute_button.click(fn=execute_transaction, inputs=[action_dropdown, ticker_input, quantity_input, price_input], outputs=execute_output)

    return demo


if __name__ == "__main__":
    ui = build_ui()
    ui.launch()


# Unit Tests
import unittest
from unittest.mock import patch

class TestTradingSimulationUI(unittest.TestCase):
    def setUp(self):
        # Reset backend data before each test
        Backend.users.clear()
        Backend.portfolios.clear()
        Backend.transactions.clear()
        current_user["username"] = None

    def test_user_registration_login(self):
        msg = register_user("alice", "alice@example.com", "pass123", "pass123")
        self.assertIn("successful", msg.lower())
        self.assertEqual(current_user["username"], "alice")

        # Test login
        current_user["username"] = None
        msg_login = login_user("alice", "pass123")
        self.assertIn("successful", msg_login.lower())
        self.assertEqual(current_user["username"], "alice")

        # Wrong password
        msg_fail = login_user("alice", "wrongpass")
        self.assertIn("invalid", msg_fail.lower())

    def test_update_profile(self):
        register_user("bob", "bob@example.com", "secret", "secret")
        # Update email only
        msg = update_profile("bob_new@example.com", "", "")
        self.assertIn("updated", msg.lower())
        self.assertEqual(Backend.users["bob"]["email"], "bob_new@example.com")

        # Update password with mismatch
        msg2 = update_profile("", "newpass", "wrong")
        self.assertIn("match", msg2.lower())

    def test_buy_sell_shares(self):
        register_user("carol", "carol@example.com", "mypassword", "mypassword")
        # Buy shares
        msg_buy = execute_transaction("Buy", "AAPL", 10, 150.0)
        self.assertIn("success", msg_buy.lower())
        portfolio = Backend.get_portfolio("carol")
        self.assertEqual(portfolio["stocks"].get("AAPL"), 10)
        # Sell shares
        msg_sell = execute_transaction("Sell", "AAPL", 5, 155.0)
        self.assertIn("success", msg_sell.lower())
        portfolio = Backend.get_portfolio("carol")
        self.assertEqual(portfolio["stocks"].get("AAPL"), 5)

        # Sell more than owned
        msg_fail = execute_transaction("Sell", "AAPL", 10, 155.0)
        self.assertIn("not enough", msg_fail.lower())

    def test_portfolio_overview_and_history(self):
        register_user("dave", "dave@example.com", "pass", "pass")
        execute_transaction("Buy", "MSFT", 10, 200.0)
        cash, stocks_str, _ = get_portfolio_overview()
        self.assertIn("Cash Balance", cash)
        self.assertIn("MSFT", stocks_str)

        header, history = get_transaction_history()
        self.assertIn("Transaction History", header)
        self.assertTrue(any("MSFT" in h for h in history))

if __name__ == "__main__":
    unittest.main(argv=['first-arg-is-ignored'], exit=False)