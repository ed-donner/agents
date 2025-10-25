import logging
import json
from flask import Flask, request, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix
from functools import wraps

from .user_management import user_manager
from .financial import financial_manager
from .trading import trading_manager
from .portfolio import portfolio_manager
from .transaction_history import transaction_history
from .price_service import price_service

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

logger = logging.getLogger(__name__)

# Authentication decorator
def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization required'}), 401
        
        # In a real implementation, this would validate a token
        # For simplicity, we'll just extract the user_id from the token
        token = auth_header.split(' ')[1]
        try:
            # Simulating token validation
            # In a real implementation, this would decode and validate a JWT
            user_id = int(token)
            return f(user_id, *args, **kwargs)
        except:
            return jsonify({'error': 'Invalid token'}), 401
    return decorated

# Error handler
@app.errorhandler(Exception)
def handle_error(e):
    logger.error(f"API error: {str(e)}")
    return jsonify({'error': str(e)}), 500

# User Routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    
    user = user_manager.create_user(username, password, email)
    if not user:
        return jsonify({'error': 'Username already exists'}), 409
    
    # Initialize balance with signup bonus
    financial_manager.deposit(user['id'], 10000.0, "Signup bonus")
    
    return jsonify({'success': True, 'user_id': user['id']}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    
    user = user_manager.authenticate_user(username, password)
    if not user:
        return jsonify({'error': 'Invalid username or password'}), 401
    
    # In a real implementation, this would generate a JWT
    # For simplicity, we'll just use the user ID as a token
    token = str(user['id'])
    return jsonify({'token': token, 'user_id': user['id']})

# Account Routes
@app.route('/api/account/profile', methods=['GET'])
@require_auth
def get_profile(user_id):
    user = user_manager.get_user_by_id(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Don't include password hash in response
    if 'password_hash' in user:
        del user['password_hash']
    
    return jsonify(user)

@app.route('/api/account/balance', methods=['GET'])
@require_auth
def get_balance(user_id):
    balance = financial_manager.get_balance(user_id)
    if balance is None:
        return jsonify({'error': 'Unable to get balance'}), 404
    
    return jsonify({'balance': balance})

# Financial Routes
@app.route('/api/financial/deposit', methods=['POST'])
@require_auth
def deposit(user_id):
    data = request.json
    amount = data.get('amount')
    description = data.get('description', 'Deposit')
    
    if not amount or not isinstance(amount, (int, float)) or amount <= 0:
        return jsonify({'error': 'Valid amount is required'}), 400
    
    success = financial_manager.deposit(user_id, amount, description)
    if not success:
        return jsonify({'error': 'Deposit failed'}), 500
    
    return jsonify({'success': True, 'new_balance': financial_manager.get_balance(user_id)})

@app.route('/api/financial/withdraw', methods=['POST'])
@require_auth
def withdraw(user_id):
    data = request.json
    amount = data.get('amount')
    description = data.get('description', 'Withdrawal')
    
    if not amount or not isinstance(amount, (int, float)) or amount <= 0:
        return jsonify({'error': 'Valid amount is required'}), 400
    
    success = financial_manager.withdraw(user_id, amount, description)
    if not success:
        return jsonify({'error': 'Withdrawal failed - insufficient funds'}), 400
    
    return jsonify({'success': True, 'new_balance': financial_manager.get_balance(user_id)})

@app.route('/api/financial/transactions', methods=['GET'])
@require_auth
def get_transactions(user_id):
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))
    transaction_type = request.args.get('type')
    
    transactions = transaction_history.get_transaction_history(
        user_id, transaction_type, limit, offset)
    
    return jsonify({'transactions': transactions})

# Trading Routes
@app.route('/api/trading/buy', methods=['POST'])
@require_auth
def buy_shares(user_id):
    data = request.json
    symbol = data.get('symbol')
    quantity = data.get('quantity')
    
    if not symbol or not quantity or not isinstance(quantity, int) or quantity <= 0:
        return jsonify({'error': 'Valid symbol and quantity are required'}), 400
    
    result = trading_manager.buy_shares(user_id, symbol, quantity)
    if not result:
        return jsonify({'error': 'Purchase failed - check balance and try again'}), 400
    
    return jsonify(result)

@app.route('/api/trading/sell', methods=['POST'])
@require_auth
def sell_shares(user_id):
    data = request.json
    symbol = data.get('symbol')
    quantity = data.get('quantity')
    
    if not symbol or not quantity or not isinstance(quantity, int) or quantity <= 0:
        return jsonify({'error': 'Valid symbol and quantity are required'}), 400
    
    result = trading_manager.sell_shares(user_id, symbol, quantity)
    if not result:
        return jsonify({'error': 'Sale failed - check holdings and try again'}), 400
    
    return jsonify(result)

@app.route('/api/trading/history', methods=['GET'])
@require_auth
def get_trade_history(user_id):
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))
    
    trades = trading_manager.get_trade_history(user_id, limit, offset)
    return jsonify({'trades': trades})

# Portfolio Routes
@app.route('/api/portfolio/holdings', methods=['GET'])
@require_auth
def get_holdings(user_id):
    holdings = portfolio_manager.get_holdings(user_id)
    return jsonify({'holdings': holdings})

@app.route('/api/portfolio/summary', methods=['GET'])
@require_auth
def get_portfolio_summary(user_id):
    summary = portfolio_manager.get_portfolio_summary(user_id)
    if not summary:
        return jsonify({'error': 'Unable to get portfolio summary'}), 500
    
    return jsonify(summary)

@app.route('/api/portfolio/allocation', methods=['GET'])
@require_auth
def get_portfolio_allocation(user_id):
    allocation = portfolio_manager.get_portfolio_allocation(user_id)
    return jsonify({'allocation': allocation})

# Price Service Routes
@app.route('/api/prices/current/<symbol>', methods=['GET'])
def get_current_price(symbol):
    price = price_service.get_current_price(symbol)
    if price is None:
        return jsonify({'error': 'Symbol not found'}), 404
    
    return jsonify({'symbol': symbol, 'price': price})

@app.route('/api/prices/historical/<symbol>', methods=['GET'])
def get_historical_prices(symbol):
    days = int(request.args.get('days', 30))
    prices = price_service.get_historical_prices(symbol, days)
    
    return jsonify({'symbol': symbol, 'prices': prices})

def create_app():
    return app
