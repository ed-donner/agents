import gradio as gr
import decimal
import time
from typing import Dict, List, TypedDict, Optional, Callable
from enum import Enum

# --- BACKEND SIMULATION (accounts module content) ---

# Configuration
PRICE_PRECISION = decimal.Decimal('0.0000')

FIXED_PRICES: Dict[str, decimal.Decimal] = {
    'AAPL': decimal.Decimal('150.0000'),
    'TSLA': decimal.Decimal('195.0000'),
    'GOOGL': decimal.Decimal('130.0000'),
    'MSFT': decimal.Decimal('300.5000'),
    'AMD': decimal.Decimal('100.0000'),
    'XOM': decimal.Decimal('500.0000')
}

def get_share_price(symbol: str) -> decimal.Decimal:
    price = FIXED_PRICES.get(symbol.upper())
    if price is None:
        raise InvalidSymbol(f"Invalid or unsupported share symbol: {symbol}")
    return price.quantize(PRICE_PRECISION)

# Define Exceptions
class AccountError(Exception): pass
class InsufficientFunds(AccountError): pass
class InsufficientHoldings(AccountError): pass
class InvalidSymbol(AccountError): pass
class InvalidAmount(AccountError): pass

# Define Data Models
class TransactionType(Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    BUY = "BUY"
    SELL = "SELL"

class TransactionRecord(TypedDict):
    id: int
    timestamp: float
    type: TransactionType
    symbol: Optional[str]
    quantity: Optional[decimal.Decimal]
    price: Optional[decimal.Decimal]
    amount: decimal.Decimal
    details: str

class HoldingDetail(TypedDict):
    symbol: str
    quantity: decimal.Decimal
    current_price: decimal.Decimal
    market_value: decimal.Decimal

class PortfolioSummary(TypedDict):
    cash_balance: decimal.Decimal
    total_market_value: decimal.Decimal
    total_portfolio_value: decimal.Decimal
    total_deposits_baseline: decimal.Decimal
    profit_loss: decimal.Decimal

# Define Account Class
class Account:
    def __init__(self, user_id: str):
        self.user_id: str = user_id
        self._ZERO: decimal.Decimal = decimal.Decimal('0.0000')
        self.cash_balance: decimal.Decimal = self._ZERO
        self.holdings: Dict[str, decimal.Decimal] = {} 
        self.transactions: List[TransactionRecord] = []
        self.deposits_baseline: decimal.Decimal = self._ZERO
        self._transaction_counter: int = 0

    def _validate_positive_amount(self, amount: decimal.Decimal, is_quantity: bool = False) -> None:
        if amount <= self._ZERO:
            msg = "Quantity must be positive." if is_quantity else "Amount must be positive."
            raise InvalidAmount(msg)

    def _log_transaction(
        self,
        tx_type: TransactionType,
        amount_impact: decimal.Decimal,
        details: str,
        symbol: Optional[str] = None,
        quantity: Optional[decimal.Decimal] = None,
        price: Optional[decimal.Decimal] = None
    ) -> None:
        self._transaction_counter += 1
        record: TransactionRecord = {
            'id': self._transaction_counter,
            'timestamp': time.time(),
            'type': tx_type,
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'amount': amount_impact.quantize(PRICE_PRECISION),
            'details': details
        }
        self.transactions.append(record)

    def deposit(self, amount: decimal.Decimal) -> None:
        amount = amount.quantize(PRICE_PRECISION)
        self._validate_positive_amount(amount)
        self.cash_balance += amount
        self.deposits_baseline += amount
        self._log_transaction(tx_type=TransactionType.DEPOSIT, amount_impact=amount, details=f"Deposit of {amount}")

    def withdraw(self, amount: decimal.Decimal) -> None:
        amount = amount.quantize(PRICE_PRECISION)
        self._validate_positive_amount(amount)
        if amount > self.cash_balance:
            raise InsufficientFunds("Insufficient funds")
        self.cash_balance -= amount
        self._log_transaction(tx_type=TransactionType.WITHDRAWAL, amount_impact=-amount, details=f"Withdrawal of {amount}")

    def buy_shares(self, symbol: str, quantity: decimal.Decimal) -> None:
        symbol = symbol.upper()
        quantity = quantity.quantize(PRICE_PRECISION)
        self._validate_positive_amount(quantity, is_quantity=True)
        price = get_share_price(symbol)
        total_cost = (price * quantity).quantize(PRICE_PRECISION)
        if total_cost > self.cash_balance:
            raise InsufficientFunds("Insufficient funds to cover trade cost")
        self.cash_balance -= total_cost
        self.holdings[symbol] = self.holdings.get(symbol, self._ZERO) + quantity
        self._log_transaction(tx_type=TransactionType.BUY, amount_impact=-total_cost, details=f"Bought {quantity} of {symbol} @ {price}", symbol=symbol, quantity=quantity, price=price)

    def sell_shares(self, symbol: str, quantity: decimal.Decimal) -> None:
        symbol = symbol.upper()
        quantity = quantity.quantize(PRICE_PRECISION)
        self._validate_positive_amount(quantity, is_quantity=True)
        current_holding = self.holdings.get(symbol, self._ZERO)
        if quantity > current_holding:
            raise InsufficientHoldings(f"Insufficient holdings for {symbol}")
        price = get_share_price(symbol)
        total_proceeds = (price * quantity).quantize(PRICE_PRECISION)
        self.cash_balance += total_proceeds
        new_holding = current_holding - quantity
        if new_holding <= self._ZERO:
            del self.holdings[symbol]
        else:
            self.holdings[symbol] = new_holding
        self._log_transaction(tx_type=TransactionType.SELL, amount_impact=total_proceeds, details=f"Sold {quantity} of {symbol} @ {price}", symbol=symbol, quantity=quantity, price=price)

    def get_transaction_history(self) -> List[TransactionRecord]:
        return self.transactions

    def get_holdings_report(self) -> Dict[str, HoldingDetail]:
        report: Dict[str, HoldingDetail] = {}
        for symbol, quantity in self.holdings.items():
            if quantity <= self._ZERO: continue
            try:
                current_price = get_share_price(symbol)
            except InvalidSymbol:
                current_price = self._ZERO
            market_value = (quantity * current_price).quantize(PRICE_PRECISION)
            report[symbol] = {
                'symbol': symbol,
                'quantity': quantity,
                'current_price': current_price,
                'market_value': market_value
            }
        return report

    def get_portfolio_summary(self) -> PortfolioSummary:
        holdings_report = self.get_holdings_report()
        total_market_value = sum([detail['market_value'] for detail in holdings_report.values()], self._ZERO).quantize(PRICE_PRECISION)
        total_portfolio_value = (self.cash_balance + total_market_value).quantize(PRICE_PRECISION)
        profit_loss = (total_portfolio_value - self.deposits_baseline).quantize(PRICE_PRECISION)
        return {
            'cash_balance': self.cash_balance,
            'total_market_value': total_market_value,
            'total_portfolio_value': total_portfolio_value,
            'total_deposits_baseline': self.deposits_baseline,
            'profit_loss': profit_loss
        }

# --- END OF BACKEND SIMULATION ---


# --- APP STATE & GRADIO WRAPPERS ---

# Global Account instance for demo state persistence
ACCOUNT = Account(user_id="GradioDemoUser")
SUPPORTED_SYMBOLS = list(FIXED_PRICES.keys())

def format_decimal(d: decimal.Decimal) -> str:
    """Formats Decimal for clean UI display."""
    if d is None: return "N/A"
    return f"${d:,.2f}"

def format_pnl_color(pnl: decimal.Decimal) -> str:
    """Returns an HTML string for colored P&L display."""
    color = "green" if pnl >= 0 else "red"
    pnl_value = format_decimal(pnl)
    return f'<p style="font-size: 1.5em; color: {color}; font-weight: bold;">Profit/Loss: {pnl_value}</p>'

def perform_deposit(amount_str: str):
    try:
        if not amount_str or float(amount_str) <= 0:
            raise InvalidAmount("Amount must be a positive number.")
            
        amount = decimal.Decimal(amount_str).quantize(PRICE_PRECISION)
        ACCOUNT.deposit(amount)
        
        return "Success: Deposit completed.", update_summary_components()[0]
    
    except (AccountError, ValueError, TypeError) as e:
        error_message = str(e)
        if "Invalid literal for Decimal" in error_message or "could not convert" in error_message:
             error_message = "Invalid input format. Please enter a valid number."
        
        return f"ERROR: {error_message}", update_summary_components()[0]

def perform_withdrawal(amount_str: str):
    try:
        if not amount_str or float(amount_str) <= 0:
            raise InvalidAmount("Amount must be a positive number.")
            
        amount = decimal.Decimal(amount_str).quantize(PRICE_PRECISION)
        ACCOUNT.withdraw(amount)
        
        return "Success: Withdrawal completed.", update_summary_components()[0]
    
    except (AccountError, ValueError, TypeError) as e:
        error_message = str(e)
        if "Invalid literal for Decimal" in error_message or "could not convert" in error_message:
             error_message = "Invalid input format. Please enter a valid number."
        
        return f"ERROR: {error_message}", update_summary_components()[0]

def perform_buy(symbol: str, quantity_str: str):
    try:
        if not quantity_str or float(quantity_str) <= 0:
            raise InvalidAmount("Quantity must be positive.")
            
        quantity = decimal.Decimal(quantity_str).quantize(PRICE_PRECISION)
        ACCOUNT.buy_shares(symbol, quantity)
        
        return "Success: Purchase completed.", update_summary_components()[0]
        
    except (AccountError, ValueError) as e:
        error_message = str(e)
        if "Invalid literal for Decimal" in error_message or "could not convert" in error_message:
             error_message = "Invalid input format for quantity."
        return f"ERROR: {error_message}", update_summary_components()[0]


def perform_sell(symbol: str, quantity_str: str):
    try:
        if not quantity_str or float(quantity_str) <= 0:
            raise InvalidAmount("Quantity must be positive.")
            
        quantity = decimal.Decimal(quantity_str).quantize(PRICE_PRECISION)
        ACCOUNT.sell_shares(symbol, quantity)
        
        return "Success: Sale completed.", update_summary_components()[0]
        
    except (AccountError, ValueError) as e:
        error_message = str(e)
        if "Invalid literal for Decimal" in error_message or "could not convert" in error_message:
             error_message = "Invalid input format for quantity."
        return f"ERROR: {error_message}", update_summary_components()[0]

def get_transaction_history_display():
    """Formats transaction history for Gradio DataFrame/Table."""
    history = ACCOUNT.get_transaction_history()
    
    # Reverse to show newest transactions first
    history.reverse()
    
    table_data = []
    
    for tx in history:
        table_data.append([
            tx['id'],
            time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(tx['timestamp'])),
            tx['type'].value,
            tx['symbol'] if tx['symbol'] else 'N/A',
            str(tx['quantity']) if tx['quantity'] else 'N/A', 
            format_decimal(tx['price']) if tx['price'] else 'N/A',
            format_decimal(tx['amount']),
            tx['details']
        ])
    
    headers = [
        "ID", "Timestamp", "Type", "Symbol", "Quantity", "Price", 
        "Cash Impact", "Details"
    ]
    return headers, table_data

def get_holdings_report_display():
    """Formats the holdings report for Gradio Table."""
    report = ACCOUNT.get_holdings_report()
    
    if not report:
        return ["Symbol", "Quantity", "Current Price", "Market Value"], []

    table_data = []
    for symbol, detail in report.items():
        table_data.append([
            symbol,
            str(detail['quantity']),
            format_decimal(detail['current_price']),
            format_decimal(detail['market_value'])
        ])

    headers = ["Symbol", "Quantity", "Current Price", "Market Value"]
    return headers, table_data


def update_summary_components():
    """Fetches summary, updates formatting, and returns components for interface update."""
    summary = ACCOUNT.get_portfolio_summary()

    # 1. Dashboard Values
    cash_bal = format_decimal(summary['cash_balance'])
    tmv = format_decimal(summary['total_market_value'])
    tpv = format_decimal(summary['total_portfolio_value'])
    pnl_html = format_pnl_color(summary['profit_loss'])
    baseline = format_decimal(summary['total_deposits_baseline'])

    # 2. Holdings Table
    _, holdings_data = get_holdings_report_display()
    
    # 3. History Table
    _, history_data = get_transaction_history_display()

    return (
        tpv, cash_bal, tmv, pnl_html, baseline, 
        holdings_data, history_data
    )

# --- GRADIO INTERFACE DEFINITION ---

with gr.Blocks(title="Trading Account Simulation") as app:
    
    with gr.Row():
        gr.Markdown(
            """
            # High-Precision Account Management Demo
            A simulation demonstrating robust financial backend operations using `decimal.Decimal`.
            The system enforces critical rules: no overdrafts (cash) and no short-selling (holdings).
            """
        )
    
    # --- Shared State Outputs ---
    with gr.Row(variant="panel"):
        tpv_output = gr.Textbox(label="Total Portfolio Value (TPV)", value=format_decimal(decimal.Decimal(0)), interactive=False, scale=1)
        cash_output = gr.Textbox(label="Cash Balance", value=format_decimal(decimal.Decimal(0)), interactive=False, scale=1)
        tmv_output = gr.Textbox(label="Total Market Value", value=format_decimal(decimal.Decimal(0)), interactive=False, scale=1)
        baseline_output = gr.Textbox(label="Deposits Baseline", value=format_decimal(decimal.Decimal(0)), interactive=False, scale=1)
        
    pnl_output = gr.Markdown(value=format_pnl_color(decimal.Decimal(0)))
    
    # Initialize state update button (hidden, for chaining)
    refresh_btn = gr.Button("Refresh State", visible=False)

    # --- TABS ---
    with gr.Tabs():
        
        # -----------------------------------------------------
        # TAB 1: Dashboard and Holdings
        # -----------------------------------------------------
        with gr.TabItem("📈 Dashboard & Holdings"):
            
            gr.Markdown("## Current Holdings")
            
            holdings_table = gr.Dataframe(
                headers=["Symbol", "Quantity", "Current Price", "Market Value"],
                datatype=["str", "str", "str", "str"],
                label="Current Share Holdings",
                interactive=False,
                row_number=False,
                wrap=True
            )
            
            gr.Markdown("### Quick Start Demo")
            gr.Examples(
                examples=[
                    ["5000.00", "AAPL", "10"], # Deposit 5k, Buy 10 AAPL
                    ["1000.00", "TSLA", "2"]  # Deposit 1k, Buy 2 TSLA
                ],
                inputs=[
                    gr.Textbox(label="Initial Deposit Amount"), 
                    gr.Dropdown(label="Symbol to Buy", choices=SUPPORTED_SYMBOLS),
                    gr.Textbox(label="Quantity to Buy")
                ],
                fn=lambda d, s, q: (perform_deposit(d)[0], perform_buy(s, q)[0]),
                outputs=[gr.Textbox(label="Deposit Result"), gr.Textbox(label="Buy Result")],
                label="Run this section to populate the account for testing."
            )


        # -----------------------------------------------------
        # TAB 2: Funds Management
        # -----------------------------------------------------
        with gr.TabItem("💰 Funds"):
            
            with gr.Row():
                with gr.Column(min_width=300):
                    gr.Markdown("### Deposit Funds (Credit)")
                    deposit_amount = gr.Textbox(
                        label="Deposit Amount ($)", 
                        value="100.00", 
                        info="Enter a positive numeric value."
                    )
                    deposit_btn = gr.Button("Execute Deposit", variant="primary")
                    deposit_output = gr.Textbox(label="Status", interactive=False)
                    
                with gr.Column(min_width=300):
                    gr.Markdown("### Withdraw Funds (Debit)")
                    withdraw_amount = gr.Textbox(
                        label="Withdrawal Amount ($)", 
                        value="10.00", 
                        info="Ensure amount <= Cash Balance (Insufficient Funds check enforced)."
                    )
                    withdraw_btn = gr.Button("Execute Withdrawal", variant="stop")
                    withdraw_output = gr.Textbox(label="Status", interactive=False)
                    
            # Link deposit actions
            deposit_btn.click(
                fn=perform_deposit, 
                inputs=[deposit_amount], 
                outputs=[deposit_output, refresh_btn]
            )

            # Link withdrawal actions
            withdraw_btn.click(
                fn=perform_withdrawal, 
                inputs=[withdraw_amount], 
                outputs=[withdraw_output, refresh_btn]
            )


        # -----------------------------------------------------
        # TAB 3: Trading
        # -----------------------------------------------------
        with gr.TabItem("📊 Trading"):

            with gr.Row():
                with gr.Column(min_width=300):
                    gr.Markdown("### Buy Shares")
                    buy_symbol = gr.Dropdown(
                        label="Stock Symbol", 
                        choices=SUPPORTED_SYMBOLS, 
                        value='AAPL',
                        info="Supported symbols: " + ", ".join(SUPPORTED_SYMBOLS)
                    )
                    buy_quantity = gr.Textbox(
                        label="Quantity to Buy", 
                        value="5", 
                        info="Total Cost = Quantity * Current Price. Requires sufficient cash."
                    )
                    buy_btn = gr.Button("Execute Buy Order", variant="primary")
                    buy_output = gr.Textbox(label="Status", interactive=False)

                with gr.Column(min_width=300):
                    gr.Markdown("### Sell Shares")
                    sell_symbol = gr.Dropdown(
                        label="Stock Symbol", 
                        choices=SUPPORTED_SYMBOLS, 
                        value='AAPL',
                        info="Select a symbol you currently hold."
                    )
                    sell_quantity = gr.Textbox(
                        label="Quantity to Sell", 
                        value="1", 
                        info="Quantity must not exceed current holdings (No short-selling)."
                    )
                    sell_btn = gr.Button("Execute Sell Order", variant="stop")
                    sell_output = gr.Textbox(label="Status", interactive=False)
                    
            # Link buy actions
            buy_btn.click(
                fn=perform_buy, 
                inputs=[buy_symbol, buy_quantity], 
                outputs=[buy_output, refresh_btn]
            )

            # Link sell actions
            sell_btn.click(
                fn=perform_sell, 
                inputs=[sell_symbol, sell_quantity], 
                outputs=[sell_output, refresh_btn]
            )

        # -----------------------------------------------------
        # TAB 4: Transaction History
        # -----------------------------------------------------
        with gr.TabItem("📜 History"):
            
            history_table = gr.Dataframe(
                headers=["ID", "Timestamp", "Type", "Symbol", "Quantity", "Price", "Cash Impact", "Details"],
                datatype=["str", "str", "str", "str", "str", "str", "str", "str"],
                label="Full Transaction History (Newest first)",
                interactive=False,
                row_number=True,
                wrap=True
            )
            gr.Markdown(
                """
                Note: Cash Impact is positive for credits (Deposit, Sell) and negative for debits (Withdrawal, Buy).
                Quantities and prices are displayed with high precision.
                """
            )


    # --- STATE REFRESH LOGIC ---
    
    SUMMARY_OUTPUTS = [
        tpv_output, cash_output, tmv_output, pnl_output, baseline_output, 
        holdings_table, history_table
    ]

    # 1. Chained refresh trigger (executed after deposit, withdraw, buy, sell)
    refresh_btn.click(
        fn=update_summary_components, 
        inputs=[], 
        outputs=SUMMARY_OUTPUTS,
        queue=False
    )

    # 2. Initial load
    app.load(
        fn=update_summary_components, 
        inputs=[], 
        outputs=SUMMARY_OUTPUTS,
        queue=False
    )
    
if __name__ == "__main__":
    app.launch()