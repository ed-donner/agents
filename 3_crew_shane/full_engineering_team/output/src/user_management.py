import bcrypt
import sqlite3
from datetime import datetime
from database import db

class UserError(Exception):
    """Base class for user management errors"""
    pass

class UserAlreadyExistsError(UserError):
    """Raised when attempting to create a user that already exists"""
    pass

class UserNotFoundError(UserError):
    """Raised when a user cannot be found"""
    pass

class AuthenticationError(UserError):
    """Raised when authentication fails"""
    pass

class UserAccount:
    """Handles user creation, login, and authentication"""
    
    @staticmethod
    def create_user(username, password, email=None):
        """Create a new user account
        
        Args:
            username (str): Unique username
            password (str): User password (will be hashed)
            email (str, optional): User email address
        
        Returns:
            int: User ID of the created user
            
        Raises:
            UserAlreadyExistsError: If the username already exists
        """
        try:
            # Hash the password
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            with db.get_cursor() as cursor:
                # Insert user
                cursor.execute(
                    "INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)",
                    (username, password_hash.decode('utf-8'), email)
                )
                user_id = cursor.lastrowid
                
                # Create initial balance record
                cursor.execute(
                    "INSERT INTO balances (user_id, amount) VALUES (?, 0.0)",
                    (user_id,)
                )
                
                return user_id
                
        except sqlite3.IntegrityError:
            raise UserAlreadyExistsError(f"User with username '{username}' already exists")
    
    @staticmethod
    def login(username, password):
        """Authenticate a user and return user ID if successful
        
        Args:
            username (str): Username to authenticate
            password (str): Password to verify
            
        Returns:
            int: User ID if authentication is successful
            
        Raises:
            UserNotFoundError: If no user with the given username exists
            AuthenticationError: If the password is incorrect
        """
        with db.get_cursor() as cursor:
            cursor.execute(
                "SELECT id, password_hash FROM users WHERE username = ?",
                (username,)
            )
            user = cursor.fetchone()
            
            if not user:
                raise UserNotFoundError(f"No user found with username '{username}'")
            
            # Verify password
            is_valid = bcrypt.checkpw(
                password.encode('utf-8'),
                user['password_hash'].encode('utf-8')
            )
            
            if not is_valid:
                raise AuthenticationError("Invalid password")
            
            return user['id']
    
    @staticmethod
    def get_user_details(user_id):
        """Get user account details
        
        Args:
            user_id (int): ID of the user to fetch
            
        Returns:
            dict: User details excluding password
            
        Raises:
            UserNotFoundError: If no user with the given ID exists
        """
        with db.get_cursor() as cursor:
            cursor.execute(
                "SELECT id, username, email, created_at FROM users WHERE id = ?",
                (user_id,)
            )
            user = cursor.fetchone()
            
            if not user:
                raise UserNotFoundError(f"No user found with ID '{user_id}'")
            
            return dict(user)
    
    @staticmethod
    def update_user(user_id, email=None, password=None):
        """Update user details
        
        Args:
            user_id (int): ID of the user to update
            email (str, optional): New email address
            password (str, optional): New password
            
        Returns:
            bool: True if update was successful
            
        Raises:
            UserNotFoundError: If no user with the given ID exists
        """
        try:
            with db.get_cursor() as cursor:
                if email and password:
                    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                    cursor.execute(
                        "UPDATE users SET email = ?, password_hash = ? WHERE id = ?",
                        (email, password_hash.decode('utf-8'), user_id)
                    )
                elif email:
                    cursor.execute(
                        "UPDATE users SET email = ? WHERE id = ?",
                        (email, user_id)
                    )
                elif password:
                    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                    cursor.execute(
                        "UPDATE users SET password_hash = ? WHERE id = ?",
                        (password_hash.decode('utf-8'), user_id)
                    )
                else:
                    return False  # Nothing to update
                
                if cursor.rowcount == 0:
                    raise UserNotFoundError(f"No user found with ID '{user_id}'")
                    
                return True
                
        except sqlite3.Error as e:
            raise Exception(f"Database error: {e}")
