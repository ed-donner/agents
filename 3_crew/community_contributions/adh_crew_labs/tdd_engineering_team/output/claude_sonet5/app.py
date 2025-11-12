import gradio as gr
from accounts import Account, get_share_price, FIXED_PRICES
from decimal import Decimal
import datetime

account = Account("demo_user")

def format_decimal(value):
    return f"${value:,.4f}"

def format_transaction_history(transactions):
    if not transactions:
        return "No transactions yet."
    
    output = []
    for tx in transactions:
        timestamp = datetime.datetime.fromtimestamp(tx['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
        tx_type = tx['type'].value
        amount = format_decimal(tx['amount'])
        
        if tx_type in ['BUY', 'SELL']:
            line = f"{timestamp} | {tx_type} | {tx['symbol']} | Qty: {tx['quantity']} | Price: {format_decimal(tx['price'])} | Amount: {amount}"
        else:
            line = f"{timestamp} | {tx_type} | Amount: {amount}"
        
        output.append(line)
    
    return "\n".join(output)

def format_holdings_report(holdings_dict):
    if not holdings_dict:
        return "No holdings."
    
    output = ["Symbol | Quantity | Current Price | Market Value"]
    output.append("-" * 60)
    
    for symbol, details in holdings_dict.items():
        line = f"{details['symbol']} | {details['quantity']} | {format_decimal(details['current_price'])} | {format_decimal(details['market_value'])}"
        output.append(line)
    
    return "\n".join(output)

def format_portfolio_summary(summary):
    pnl = summary['profit_loss']
    pnl_color = "🟢" if pnl >= 0 else "🔴"
    
    output = [
        f"💰 Cash Balance: {format_decimal(summary['cash_balance'])}",
        f"📊 Total Market Value: {format_decimal(summary['total_market_value'])}",
        f"💼 Total Portfolio Value: {format_decimal(summary['total_portfolio_value'])}",
        f"📥 Total Deposits: {format_decimal(summary['total_deposits_baseline'])}",
        f"{pnl_color} Profit/Loss: {format_decimal(pnl)}"
    ]
    
    return "\n".join(output)

def get_current_balance():
    return format_decimal(account.cash_balance)

def deposit_funds(amount_str):
    try:
        amount = Decimal(amount_str)
        account.deposit(amount)
        return f"✅ Successfully deposited {format_decimal(amount)}\n\nNew Balance: {get_current_balance()}", get_current_balance()
    except ValueError:
        return "❌ Error: Invalid amount format. Please enter a valid number.", get_current_balance()
    except Exception as e:
        return f"❌ Error: {str(e)}", get_current_balance()

def withdraw_funds(amount_str):
    try:
        amount = Decimal(amount_str)
        account.withdraw(amount)
        return f"✅ Successfully withdrew {format_decimal(amount)}\n\nNew Balance: {get_current_balance()}", get_current_balance()
    except ValueError:
        return "❌ Error: Invalid amount format. Please enter a valid number.", get_current_balance()
    except Exception as e:
        return f"❌ Error: {str(e)}", get_current_balance()

def buy_shares_action(symbol, quantity_str):
    try:
        quantity = Decimal(quantity_str)
        price = get_share_price(symbol)
        total_cost = price * quantity
        
        account.buy_shares(symbol, quantity)
        return f"✅ Successfully bought {quantity} shares of {symbol}\n\nPrice per share: {format_decimal(price)}\nTotal cost: {format_decimal(total_cost)}\n\nNew Balance: {get_current_balance()}", get_current_balance()
    except ValueError:
        return "❌ Error: Invalid quantity format. Please enter a valid number.", get_current_balance()
    except Exception as e:
        return f"❌ Error: {str(e)}", get_current_balance()

def sell_shares_action(symbol, quantity_str):
    try:
        quantity = Decimal(quantity_str)
        price = get_share_price(symbol)
        total_proceeds = price * quantity
        
        account.sell_shares(symbol, quantity)
        return f"✅ Successfully sold {quantity} shares of {symbol}\n\nPrice per share: {format_decimal(price)}\nTotal proceeds: {format_decimal(total_proceeds)}\n\nNew Balance: {get_current_balance()}", get_current_balance()
    except ValueError:
        return "❌ Error: Invalid quantity format. Please enter a valid number.", get_current_balance()
    except Exception as e:
        return f"❌ Error: {str(e)}", get_current_balance()

def get_holdings():
    holdings_dict = account.get_holdings_report()
    return format_holdings_report(holdings_dict)

def get_portfolio():
    summary = account.get_portfolio_summary()
    return format_portfolio_summary(summary)

def get_transactions():
    history = account.get_transaction_history()
    return format_transaction_history(history)

def get_stock_price(symbol):
    try:
        price = get_share_price(symbol)
        return f"Current price of {symbol}: {format_decimal(price)}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

def get_available_symbols():
    return ", ".join(sorted(FIXED_PRICES.keys()))

def run_demo_scenario():
    try:
        account.deposit(Decimal('10000.00'))
        account.buy_shares('AAPL', Decimal('20'))
        account.buy_shares('TSLA', Decimal('10'))
        account.sell_shares('AAPL', Decimal('5'))
        account.withdraw(Decimal('1000.00'))
        
        return "✅ Demo scenario completed!\n\nActions performed:\n1. Deposited $10,000\n2. Bought 20 shares of AAPL\n3. Bought 10 shares of TSLA\n4. Sold 5 shares of AAPL\n5. Withdrew $1,000\n\nCheck the Portfolio tab to see results!", get_current_balance()
    except Exception as e:
        return f"❌ Error running demo: {str(e)}", get_current_balance()

with gr.Blocks(title="Trading Simulation Platform", theme=gr.themes.Soft()) as app:
    gr.Markdown("""
    # 📈 Trading Simulation Platform
    
    A complete account management system for simulating stock trading with real-time portfolio tracking.
    
    **Features:**
    - Deposit and withdraw funds with overdraft protection
    - Buy and sell shares with affordability and possession checks
    - Real-time portfolio valuation and P&L tracking
    - Comprehensive transaction history
    
    **Supported Symbols:** {}
    """.format(get_available_symbols()))
    
    current_balance_display = gr.Textbox(
        label="💰 Current Cash Balance",
        value=get_current_balance(),
        interactive=False,
        scale=1
    )
    
    with gr.Tabs():
        with gr.Tab("💵 Funds Management"):
            gr.Markdown("### Deposit or withdraw funds from your account")
            
            with gr.Row():
                with gr.Column():
                    gr.Markdown("#### Deposit Funds")
                    deposit_amount = gr.Textbox(
                        label="Amount to Deposit",
                        placeholder="1000.00",
                        info="Enter amount in USD (e.g., 1000.00)"
                    )
                    deposit_btn = gr.Button("💰 Deposit", variant="primary")
                    deposit_output = gr.Textbox(label="Result", lines=4)
                
                with gr.Column():
                    gr.Markdown("#### Withdraw Funds")
                    withdraw_amount = gr.Textbox(
                        label="Amount to Withdraw",
                        placeholder="500.00",
                        info="Cannot exceed current balance"
                    )
                    withdraw_btn = gr.Button("💸 Withdraw", variant="secondary")
                    withdraw_output = gr.Textbox(label="Result", lines=4)
            
            deposit_btn.click(
                deposit_funds,
                inputs=[deposit_amount],
                outputs=[deposit_output, current_balance_display]
            )
            
            withdraw_btn.click(
                withdraw_funds,
                inputs=[withdraw_amount],
                outputs=[withdraw_output, current_balance_display]
            )
        
        with gr.Tab("📊 Trading"):
            gr.Markdown("### Buy and sell shares")
            
            with gr.Row():
                with gr.Column():
                    gr.Markdown("#### Buy Shares")
                    buy_symbol = gr.Dropdown(
                        choices=sorted(FIXED_PRICES.keys()),
                        label="Stock Symbol",
                        info="Select a stock to buy"
                    )
                    buy_quantity = gr.Textbox(
                        label="Quantity",
                        placeholder="10",
                        info="Number of shares to buy"
                    )
                    buy_btn = gr.Button("📈 Buy Shares", variant="primary")
                    buy_output = gr.Textbox(label="Result", lines=6)
                
                with gr.Column():
                    gr.Markdown("#### Sell Shares")
                    sell_symbol = gr.Dropdown(
                        choices=sorted(FIXED_PRICES.keys()),
                        label="Stock Symbol",
                        info="Select a stock to sell"
                    )
                    sell_quantity = gr.Textbox(
                        label="Quantity",
                        placeholder="5",
                        info="Number of shares to sell"
                    )
                    sell_btn = gr.Button("📉 Sell Shares", variant="secondary")
                    sell_output = gr.Textbox(label="Result", lines=6)
            
            with gr.Row():
                price_symbol = gr.Dropdown(
                    choices=sorted(FIXED_PRICES.keys()),
                    label="Check Stock Price",
                    scale=2
                )
                price_btn = gr.Button("🔍 Get Price", scale=1)
                price_output = gr.Textbox(label="Price", scale=2)
            
            buy_btn.click(
                buy_shares_action,
                inputs=[buy_symbol, buy_quantity],
                outputs=[buy_output, current_balance_display]
            )
            
            sell_btn.click(
                sell_shares_action,
                inputs=[sell_symbol, sell_quantity],
                outputs=[sell_output, current_balance_display]
            )
            
            price_btn.click(
                get_stock_price,
                inputs=[price_symbol],
                outputs=[price_output]
            )
        
        with gr.Tab("💼 Portfolio"):
            gr.Markdown("### View your portfolio summary and holdings")
            
            portfolio_btn = gr.Button("🔄 Refresh Portfolio", variant="primary")
            
            with gr.Row():
                portfolio_summary = gr.Textbox(
                    label="Portfolio Summary",
                    lines=8,
                    interactive=False
                )
                holdings_display = gr.Textbox(
                    label="Current Holdings",
                    lines=8,
                    interactive=False
                )
            
            portfolio_btn.click(
                lambda: (get_portfolio(), get_holdings()),
                outputs=[portfolio_summary, holdings_display]
            )
        
        with gr.Tab("📜 Transaction History"):
            gr.Markdown("### View all account transactions")
            
            history_btn = gr.Button("🔄 Refresh History", variant="primary")
            history_display = gr.Textbox(
                label="Transaction History",
                lines=15,
                interactive=False
            )
            
            history_btn.click(
                get_transactions,
                outputs=[history_display]
            )
        
        with gr.Tab("🎮 Demo"):
            gr.Markdown("""
            ### Try a Quick Demo
            
            Run a pre-configured demo scenario to see all features in action:
            
            1. **Deposit** $10,000
            2. **Buy** 20 shares of AAPL
            3. **Buy** 10 shares of TSLA
            4. **Sell** 5 shares of AAPL
            5. **Withdraw** $1,000
            
            After running the demo, check the Portfolio tab to see your holdings and P&L!
            """)
            
            demo_btn = gr.Button("🚀 Run Demo Scenario", variant="primary", size="lg")
            demo_output = gr.Textbox(label="Demo Results", lines=10)
            
            demo_btn.click(
                run_demo_scenario,
                outputs=[demo_output, current_balance_display]
            )
    
    gr.Markdown("""
    ---
    ### 📖 Usage Tips
    
    - **Deposits** must be positive amounts
    - **Withdrawals** cannot exceed your current balance (overdraft protection)
    - **Buying shares** requires sufficient cash balance
    - **Selling shares** requires you to own the shares (no short selling)
    - All amounts use high-precision decimal calculations
    - P&L is calculated as: (Total Portfolio Value) - (Total Deposits)
    
    ### 🎯 Example Workflows
    
    1. **Getting Started:** Go to Funds Management → Deposit $5,000
    2. **First Trade:** Go to Trading → Buy 10 shares of AAPL
    3. **Check Performance:** Go to Portfolio → Refresh Portfolio
    4. **View Activity:** Go to Transaction History → Refresh History
    """)

if __name__ == "__main__":
    app.launch()