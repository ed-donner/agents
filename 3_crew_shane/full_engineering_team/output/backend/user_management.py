import bcrypt
import logging
from datetime import datetime
from .database import db

class UserManagement:
    def __init__(self):
        """Initialize user management module."""
        self.logger = logging.getLogger(__name__)
    
    def create_user(self, username, password, email=None):
        """Create a new user account.
        
        Args:
            username (str): Unique username
            password (str): User password
            email (str, optional): User email address
            
        Returns:
            dict: User information on success, None on failure
        """
        try:
            # Hash the password
            password_hash = self._hash_password(password)
            
            with db.get_cursor() as cursor:
                # Insert user
                cursor.execute(
                    "INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)",
                    (username, password_hash, email)
                )
                user_id = cursor.lastrowid
                
                # Initialize balance for the user
                cursor.execute(
                    "INSERT INTO balances (user_id, amount) VALUES (?, ?)",
                    (user_id, 0.0)
                )
                
                return self.get_user_by_id(user_id)
        except Exception as e:
            self.logger.error(f"Error creating user: {e}")
            return None
    
    def authenticate_user(self, username, password):
        """Authenticate a user by username and password.
        
        Args:
            username (str): Username
            password (str): Password
            
        Returns:
            dict: User information if authentication successful, None otherwise
        """
        try:
            with db.get_cursor() as cursor:
                cursor.execute(
                    "SELECT id, username, password_hash FROM users WHERE username = ?",
                    (username,)
                )
                user = cursor.fetchone()
                
                if user and self._verify_password(password, user['password_hash']):
                    return {
                        'id': user['id'],
                        'username': user['username']
                    }
                return None
        except Exception as e:
            self.logger.error(f"Error authenticating user: {e}")
            return None
    
    def get_user_by_id(self, user_id):
        """Get user information by ID.
        
        Args:
            user_id (int): User ID
            
        Returns:
            dict: User information if found, None otherwise
        """
        try:
            with db.get_cursor() as cursor:
                cursor.execute(
                    "SELECT id, username, email, created_at FROM users WHERE id = ?",
                    (user_id,)
                )
                user = cursor.fetchone()
                
                if user:
                    return dict(user)
                return None
        except Exception as e:
            self.logger.error(f"Error getting user by ID: {e}")
            return None
    
    def get_user_by_username(self, username):
        """Get user information by username.
        
        Args:
            username (str): Username
            
        Returns:
            dict: User information if found, None otherwise
        """
        try:
            with db.get_cursor() as cursor:
                cursor.execute(
                    "SELECT id, username, email, created_at FROM users WHERE username = ?",
                    (username,)
                )
                user = cursor.fetchone()
                
                if user:
                    return dict(user)
                return None
        except Exception as e:
            self.logger.error(f"Error getting user by username: {e}")
            return None
    
    def update_user(self, user_id, email=None):
        """Update user information.
        
        Args:
            user_id (int): User ID
            email (str, optional): New email address
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            with db.get_cursor() as cursor:
                update_fields = []
                params = []
                
                if email is not None:
                    update_fields.append("email = ?")
                    params.append(email)
                
                if not update_fields:
                    return True  # Nothing to update
                
                params.append(user_id)
                query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
                cursor.execute(query, params)
                
                return cursor.rowcount > 0
        except Exception as e:
            self.logger.error(f"Error updating user: {e}")
            return False
    
    def change_password(self, user_id, current_password, new_password):
        """Change a user's password.
        
        Args:
            user_id (int): User ID
            current_password (str): Current password
            new_password (str): New password
            
        Returns:
            bool: True if change successful, False otherwise
        """
        try:
            with db.get_cursor() as cursor:
                cursor.execute(
                    "SELECT password_hash FROM users WHERE id = ?",
                    (user_id,)
                )
                user = cursor.fetchone()
                
                if not user:
                    return False
                
                if not self._verify_password(current_password, user['password_hash']):
                    return False
                
                password_hash = self._hash_password(new_password)
                cursor.execute(
                    "UPDATE users SET password_hash = ? WHERE id = ?",
                    (password_hash, user_id)
                )
                
                return True
        except Exception as e:
            self.logger.error(f"Error changing password: {e}")
            return False
    
    def _hash_password(self, password):
        """Hash a password using bcrypt.
        
        Args:
            password (str): Password to hash
            
        Returns:
            str: Hashed password
        """
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def _verify_password(self, password, password_hash):
        """Verify a password against its hash.
        
        Args:
            password (str): Password to verify
            password_hash (str): Stored password hash
            
        Returns:
            bool: True if password matches, False otherwise
        """
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

# Create a singleton instance
user_manager = UserManagement()
