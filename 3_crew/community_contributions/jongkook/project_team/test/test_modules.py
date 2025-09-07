import unittest
from output.modules import Market, UserAccount, Portfolio, Transaction

class TestTradingSimulation(unittest.TestCase):

    def setUp(self):
        self.user = UserAccount("user1")
        self.portfolio = Portfolio()
        self.transaction = Transaction(self.user, self.portfolio)

    # UserAccount tests
    def test_deposit_and_withdraw(self):
        self.user.deposit(1000)
        self.assertEqual(self.user.balance, 1000)
        self.user.withdraw(200)
        self.assertEqual(self.user.balance, 800)

    def test_withdraw_insufficient_funds(self):
        self.user.deposit(100)
        with self.assertRaises(ValueError):
            self.user.withdraw(200)

    def test_deposit_negative(self):
        with self.assertRaises(ValueError):
            self.user.deposit(-50)

    def test_withdraw_negative(self):
        with self.assertRaises(ValueError):
            self.user.withdraw(-50)

    # Market tests
    def test_get_share_price(self):
        price = Market.get_share_price('AAPL')
        self.assertEqual(price, 150.0)
        with self.assertRaises(ValueError):
            Market.get_share_price('UNKNOWN')

    # Portfolio tests
    def test_add_and_remove_shares(self):
        self.portfolio.add_shares('AAPL', 10)
        self.assertEqual(self.portfolio.holdings['AAPL'], 10)
        self.portfolio.remove_shares('AAPL', 5)
        self.assertEqual(self.portfolio.holdings['AAPL'], 5)

    def test_remove_shares_too_many(self):
        self.portfolio.add_shares('TSLA', 5)
        with self.assertRaises(ValueError):
            self.portfolio.remove_shares('TSLA', 10)

    def test_calculate_total_value(self):
        self.portfolio.add_shares('AAPL', 2)  # 2*150 = 300
        self.portfolio.add_shares('GOOG', 1)  # 1*2800 = 2800
        total_value = self.portfolio.calculate_total_value()
        self.assertEqual(total_value, 3100.0)

    def test_assess_profit_loss(self):
        self.portfolio.add_shares('AAPL', 5)  # 5*150=750
        profit_loss = self.portfolio.assess_profit_loss(700)
        self.assertEqual(profit_loss, 50)

    def test_assess_profit_loss_negative_deposit(self):
        with self.assertRaises(ValueError):
            self.portfolio.assess_profit_loss(-100)

    # Transaction tests
    def test_buy_shares_success(self):
        self.user.deposit(1000)
        self.transaction.buy_shares('AAPL', 5)  # 5*150=750
        self.assertEqual(self.user.balance, 250)
        self.assertEqual(self.portfolio.holdings['AAPL'], 5)
        self.assertEqual(len(self.transaction.transactions), 1)

    def test_buy_shares_insufficient_funds(self):
        self.user.deposit(100)
        with self.assertRaises(ValueError):
            self.transaction.buy_shares('GOOG', 1)  # 2800 > 100

    def test_sell_shares_success(self):
        self.portfolio.add_shares('TSLA', 10)
        self.transaction.sell_shares('TSLA', 5)  # user not credited yet
        self.assertEqual(self.portfolio.holdings['TSLA'], 5)
        self.assertEqual(self.user.balance, 3500)  # 5*700
        self.assertEqual(len(self.transaction.transactions), 1)

    def test_sell_shares_insufficient_shares(self):
        self.portfolio.add_shares('MSFT', 2)
        with self.assertRaises(ValueError):
            self.transaction.sell_shares('MSFT', 5)

if __name__ == '__main__':
    unittest.main()