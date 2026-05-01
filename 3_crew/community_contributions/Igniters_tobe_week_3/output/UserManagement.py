from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4


@dataclass
class User:
    username: str
    email: str
    password: str
    user_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_login: datetime | None = None

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "created_at": self.created_at.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }


class AuthenticationManager:
    def __init__(self):
        self.users = {}
        self.username_lookup = {}
        self.email_lookup = {}
        self.active_sessions = {}

    def register(self, username, email, password):
        username = username.strip()
        email = email.strip().lower()
        if not username or not email or not password:
            return False, "Username, email, and password are required"
        if username in self.username_lookup:
            return False, "Username already exists"
        if email in self.email_lookup:
            return False, "Email already exists"
        user = User(username=username, email=email, password=password)
        self.users[user.user_id] = user
        self.username_lookup[username] = user.user_id
        self.email_lookup[email] = user.user_id
        return True, user.user_id

    def authenticate(self, username, password):
        username = username.strip()
        user_id = self.username_lookup.get(username)
        if not user_id:
            return False, "Invalid username or password"
        user = self.users[user_id]
        if user.password != password:
            return False, "Invalid username or password"
        user.last_login = datetime.now(UTC)
        session_id = str(uuid4())
        self.active_sessions[session_id] = user.user_id
        return True, {"session_id": session_id, "user_id": user.user_id}

    def logout(self, session_id):
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            return True, "Logged out"
        return False, "Session not found"

    def get_user(self, user_id):
        return self.users.get(user_id)

    def get_user_by_session(self, session_id):
        user_id = self.active_sessions.get(session_id)
        if not user_id:
            return None
        return self.users.get(user_id)


auth_manager = AuthenticationManager()


def register_user(username, email, password):
    return auth_manager.register(username, email, password)


def authenticate_user(username, password):
    return auth_manager.authenticate(username, password)


def logout_user(session_id):
    return auth_manager.logout(session_id)


def get_user_details(user_id):
    user = auth_manager.get_user(user_id)
    return user.to_dict() if user else None


def get_user_by_session(session_id):
    user = auth_manager.get_user_by_session(session_id)
    return user.to_dict() if user else None
