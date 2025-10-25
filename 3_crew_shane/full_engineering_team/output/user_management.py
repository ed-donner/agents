import hashlib
import os
import logging
import re
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UserManagement:
    """User management class for the trading simulation platform."""
    
    def __init__(self, database):
        """Initialize user management with database connection.
        
        Args:
            database (Database): Database instance
        """
        self.db = database
    
    def hash_password(self, password, salt=None):
        """Hash a password for storing.
        
        Args:
            password (str): The password to hash
            salt (bytes, optional): Salt for hashing. Generated if None.
            
        Returns:
            tuple: (hash, salt)
        """
        if salt is None:
            salt = os.urandom(32)  # 32 bytes salt
        
        # Use SHA-256 for password hashing (in production, use bcrypt/argon2)
        pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return pwdhash.hex(), salt.hex()
    
    def validate_password(self, stored_hash, salt, provided_password):
        """Validate a password against its stored hash.
        
        Args:
            stored_hash (str): The stored password hash
            salt (str): The salt used for hashing
            provided_password (str): The password to check
            
        Returns:
            bool: True if password is valid, False otherwise
        """
        calculated_hash, _ = self.hash_password(provided_password, bytes.fromhex(salt))
        return calculated_hash == stored_hash
    
    def validate_email(self, email):
        """Validate email format.
        
        Args:
            email (str): Email to validate
            
        Returns:
            bool: True if email is valid, False otherwise
        """
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email))
    
    def create_user(self, username, password, email):
        """Create a new user account.
        
        Args:
            username (str): Username
            password (str): Password
            email (str): Email address
            
        Returns:
            int: User ID if created, None otherwise
        """
        # Validate input
        if not username or not password or not email:
            logger.error("Missing required fields for user creation")
            return None
        
        if not self.validate_email(email):
            logger.error("Invalid email format")
            return None
        
        # Check if username or email already exists
        existing = self.db.execute_query("SELECT id FROM users WHERE username = ? OR email = ?", 
                                        (username, email))
        if existing:
            logger.error("Username or email already exists")
            return None
        
        # Hash password
        password_hash, salt = self.hash_password(password)
        combined_hash = f"{password_hash}:{salt}"  # Store both hash and salt
        
        try:
            # Insert new user
            user_id = self.db.execute_transaction(
                "INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)",
                (username, combined_hash, email))
            
            # Initialize balance
            self.db.execute_transaction(
                "INSERT INTO balances (user_id, amount) VALUES (?, 0.0)",
                (user_id,))
            
            logger.info(f"Created new user: {username}")
            return user_id
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None
    
    def authenticate_user(self, username, password):
        """Authenticate a user.
        
        Args:
            username (str): Username
            password (str): Password
            
        Returns:
            dict: User info if authenticated, None otherwise
        """
        try:
            users = self.db.execute_query(
                "SELECT id, username, password_hash, email FROM users WHERE username = ?", 
                (username,))
            
            if not users:
                logger.warning(f"Authentication failed: User {username} not found")
                return None
            
            user = users[0]
            stored_hash_salt = user['password_hash']
            stored_hash, salt = stored_hash_salt.split(':') if ':' in stored_hash_salt else (stored_hash_salt, '')
            
            if self.validate_password(stored_hash, salt, password):
                logger.info(f"User {username} authenticated successfully")
                return {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email']
                }
            else:
                logger.warning(f"Authentication failed: Invalid password for {username}")
                return None
        except Exception as e:
            logger.error(f"Error during authentication: {e}")
            return None
    
    def get_user_by_id(self, user_id):
        """Get user information by ID.
        
        Args:
            user_id (int): User ID
            
        Returns:
            dict: User information
        """
        try:
            users = self.db.execute_query(
                "SELECT id, username, email, created_at FROM users WHERE id = ?",
                (user_id,))
            
            if not users:
                return None
            
            user = users[0]
            return {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'created_at': user['created_at']
            }
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None
    
    def update_user(self, user_id, email=None, password=None):
        """Update user information.
        
        Args:
            user_id (int): User ID
            email (str, optional): New email
            password (str, optional): New password
            
        Returns:
            bool: True if updated, False otherwise
        """
        try:
            # Check if user exists
            user = self.get_user_by_id(user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return False
            
            # Update email if provided
            if email and email != user['email']:
                if not self.validate_email(email):
                    logger.error("Invalid email format")
                    return False
                
                self.db.execute_transaction(
                    "UPDATE users SET email = ? WHERE id = ?",
                    (email, user_id))
            
            # Update password if provided
            if password:
                password_hash, salt = self.hash_password(password)
                combined_hash = f"{password_hash}:{salt}"
                
                self.db.execute_transaction(
                    "UPDATE users SET password_hash = ? WHERE id = ?",
                    (combined_hash, user_id))
            
            logger.info(f"Updated user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            return False