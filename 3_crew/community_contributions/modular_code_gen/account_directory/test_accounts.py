import requests

def test_api():
    base_url = 'http://localhost:7860/'
    # Test create_account
    print(requests.post(base_url + 'create_account', json={'user_id': 'user123'}).json())
    # Test deposit
    print(requests.post(base_url + 'deposit', json={'user_id': 'user123', 'amount': 100}).json())
    # Test withdraw
    print(requests.post(base_url + 'withdraw', json={'user_id': 'user123', 'amount': 50}).json())
    # Test buy_shares
    print(requests.post(base_url + 'buy_shares', json={'user_id': 'user123', 'symbol': 'AAPL', 'quantity': 10}).json())
    # Test sell_shares
    print(requests.post(base_url + 'sell_shares', json={'user_id': 'user123', 'symbol': 'AAPL', 'quantity': 5}).json())
    # Test get_transactions
    print(requests.get(base_url + 'get_transactions', json={'user_id': 'user123'}).json())
    # Test calculate_portfolio_value
    print(requests.get(base_url + 'calculate_portfolio_value', json={'user_id': 'user123'}).json())
    # Test get_share_price
    print(requests.get(base_url + 'get_share_price', json={'symbol': 'AAPL'}).json())

test_api()