from google.adk.sessions import BaseSessionService, Session
from typing import Optional, Dict, Any, List
import datetime

# --- Enhanced InMemorySessionService ---
class InMemorySessionService(BaseSessionService):
    def __init__(self):
        self._sessions: Dict[str, tuple[Session, Dict]] = {}

    async def create_session(self, app_name: str, user_id: str, session_id: str) -> Session:
        session_key = f"{app_name}:{user_id}:{session_id}"
        if session_key not in self._sessions:
            session = Session(
                id=session_key,
                app_name=app_name,
                user_id=user_id
            )
            custom_data = {
                "history": [],
                "state": {
                    "active_agent": None,
                    "order_details": {},
                    "bill_confirmed": False,
                    "order_status_details": {}
                },
                "created_at": datetime.datetime.now().isoformat()
            }
            self._sessions[session_key] = (session, custom_data)
        return self._sessions[session_key][0]

    async def get_session(self, app_name: str, user_id: str, session_id: str, raise_error: bool = True) -> Optional[Session]:
        session_key = f"{app_name}:{user_id}:{session_id}"
        session_data = self._sessions.get(session_key)
        if not session_data and raise_error:
            raise KeyError(f"Session {session_key} not found")
        return session_data[0] if session_data else None

    async def get_custom_data(self, app_name: str, user_id: str, session_id: str) -> Optional[Dict]:
        session_key = f"{app_name}:{user_id}:{session_id}"
        session_data = self._sessions.get(session_key)
        return session_data[1] if session_data else None

    async def delete_session(self, app_name: str, user_id: str, session_id: str) -> None:
        session_key = f"{app_name}:{user_id}:{session_id}"
        if session_key in self._sessions:
            del self._sessions[session_key]

    async def list_sessions(self, app_name: str, user_id: str) -> List[Session]:
        return [
            session_data[0]
            for session_key, session_data in self._sessions.items()
            if session_data[0].app_name == app_name and session_data[0].user_id == user_id
        ]

    async def list_events(self, app_name: str, user_id: str, session_id: str) -> List[Any]:
        return []

    async def update_session(self, app_name: str, user_id: str, session_id: str, data: Dict):
        session_key = f"{app_name}:{user_id}:{session_id}"
        if session_key in self._sessions:
            session, custom_data = self._sessions[session_key]
            custom_data.update(data)
            self._sessions[session_key] = (session, custom_data)

    async def append_history(self, app_name: str, user_id: str, session_id: str, role: str, text: str):
        session_key = f"{app_name}:{user_id}:{session_id}"
        if session_key in self._sessions:
            session, custom_data = self._sessions[session_key]
            custom_data["history"].append({"role": role, "text": text})
            self._sessions[session_key] = (session, custom_data)