import sqlite3
from datetime import datetime
from database import db

class FinancialError(Exception):
    """Base class for financial operation errors"""
    pass

class InsufficientFundsError(FinancialError):
    """Raised when a withdrawal exceeds available funds"""
    pass

class InvalidAmountError(FinancialError):
    """Raised when an invalid amount is provided"""
    pass

class UserBalanceNotFoundError(FinancialError):
    """Raised when a user balance cannot be found"""
    pass

class AccountBalance:
    """Manages user balances, deposits, and withdrawals"""
    
    @staticmethod
    def get_balance(user_id):
        """Get current balance for a user
        
        Args:
            user_id (int): User ID to check balance for
            
        Returns:
            float: Current balance
            
        Raises:
            UserBalanceNotFoundError: If no balance record exists for user
        """
        with db.get_cursor() as cursor:
            cursor.execute(
                "SELECT amount FROM balances WHERE user_id = ?",
                (user_id,)
            )
            balance = cursor.fetchone()
            
            if not balance:
                raise UserBalanceNotFoundError(f"No balance found for user ID '{user_id}'")
            
            return balance['amount']
    
    @staticmethod
    def deposit(user_id, amount, description=None):
        """Add funds to user account
        
        Args:
            user_id (int): User ID to deposit to
            amount (float): Amount to deposit
            description (str, optional): Description of the deposit
            
        Returns:
            float: New balance after deposit
            
        Raises:
            InvalidAmountError: If amount is not positive
            UserBalanceNotFoundError: If no balance record exists for user
        """
        if amount <= 0:
            raise InvalidAmountError("Deposit amount must be positive")
        
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Start a transaction
                conn.execute("BEGIN EXCLUSIVE TRANSACTION")
                
                # Update balance
                cursor.execute(
                    "UPDATE balances SET amount = amount + ?, last_updated = CURRENT_TIMESTAMP WHERE user_id = ?",
                    (amount, user_id)
                )
                
                if cursor.rowcount == 0:
                    conn.rollback()
                    raise UserBalanceNotFoundError(f"No balance found for user ID '{user_id}'")
                
                # Record transaction
                cursor.execute(
                    "INSERT INTO transactions (user_id, type, amount, description) VALUES (?, 'deposit', ?, ?)",
                    (user_id, amount, description)
                )
                
                # Get updated balance
                cursor.execute("SELECT amount FROM balances WHERE user_id = ?", (user_id,))
                new_balance = cursor.fetchone()['amount']
                
                conn.commit()
                return new_balance
                
        except sqlite3.Error as e:
            conn.rollback()
            raise Exception(f"Database error: {e}")
    
    @staticmethod
    def withdraw(user_id, amount, description=None):
        """Withdraw funds from user account
        
        Args:
            user_id (int): User ID to withdraw from
            amount (float): Amount to withdraw
            description (str, optional): Description of the withdrawal
            
        Returns:
            float: New balance after withdrawal
            
        Raises:
            InvalidAmountError: If amount is not positive
            InsufficientFundsError: If withdrawal exceeds available balance
            UserBalanceNotFoundError: If no balance record exists for user
        """
        if amount <= 0:
            raise InvalidAmountError("Withdrawal amount must be positive")
        
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Start a transaction
                conn.execute("BEGIN EXCLUSIVE TRANSACTION")
                
                # Check current balance
                cursor.execute("SELECT amount FROM balances WHERE user_id = ?", (user_id,))
                balance = cursor.fetchone()
                
                if not balance:
                    conn.rollback()
                    raise UserBalanceNotFoundError(f"No balance found for user ID '{user_id}'")
                
                if balance['amount'] < amount:
                    conn.rollback()
                    raise InsufficientFundsError(f"Insufficient funds. Available: {balance['amount']}, Requested: {amount}")
                
                # Update balance
                cursor.execute(
                    "UPDATE balances SET amount = amount - ?, last_updated = CURRENT_TIMESTAMP WHERE user_id = ?",
                    (amount, user_id)
                )
                
                # Record transaction
                cursor.execute(
                    "INSERT INTO transactions (user_id, type, amount, description) VALUES (?, 'withdrawal', ?, ?)",
                    (user_id, amount, description)
                )
                
                # Get updated balance
                cursor.execute("SELECT amount FROM balances WHERE user_id = ?", (user_id,))
                new_balance = cursor.fetchone()['amount']
                
                conn.commit()
                return new_balance
                
        except sqlite3.Error as e:
            conn.rollback()
            raise Exception(f"Database error: {e}")
