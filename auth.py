import base64
from datetime import datetime
from typing import Any
import sqlalchemy.orm
import typing

import handler
import model
import password as pwd


class AuthManager:
    session: sqlalchemy.orm.Session

    def __init__(self, session: sqlalchemy.orm.Session):
        self.session = session

    def register(self, username: str, password: str) -> model.User:
        count = self.session.query(model.User) \
            .filter_by(username=username) \
            .count()
        if count > 0:
            raise ValueError("Username taken")
        user = model.User.new(username, password)
        self.session.add(user)
        return user

    def login(self, username: str, password: str) -> typing.Tuple[model.LoginSession, str]:
        user: model.User = self.session.query(model.User) \
            .filter_by(username=username) \
            .one_or_none()
        if user is None:
            raise ValueError("Invalid username or password")
        if not pwd.compare(password, user.password):
            raise ValueError("Invalid username or password")
        login_session, key = model.LoginSession.new(user)
        self.session.add(login_session)
        return login_session, key
    
    def logout(self, session_id: int):
        session = self.session.query(model.LoginSession) \
            .filter_by(id=session_id) \
            .one_or_none()
        self.session.delete(session)


class AuthRequestHandler(handler.BaseRequestHandler):
    user_id: int|None = None
    login_session_id: int|None = None

    def _decode_session(self, auth_str: str) -> typing.Tuple[str, str]:
        parts: typing.List[str] = auth_str.split(":")
        if len(parts) == 2:
            return parts[0], parts[1]
        return None, None
    
    def _encode_session(self, session_id: str, session_key: str) -> str:
        return base64.b64encode(f"{session_id}:{session_key}".encode("ascii")).decode("ascii")

    def _get_cookie_session_params(self):
        base64_auth_str: str|None = self.get_secure_cookie("authorization", None)
        if base64_auth_str is None:
            return None, None
        auth_str = base64.b64decode(base64_auth_str).decode("ascii")
        return self._decode_session(auth_str)

    def _get_header_session_params(self):
        auth_str: str|None = self.request.headers.get("Authorization", None)
        if auth_str is None:
            return None, None
        if not auth_str.startswith("Bearer"):
            return None, None
        if len(auth_str) <= 6:
            return None, None
        base64_auth_str = auth_str[6:]
        raw_auth_str = base64.b64decode(base64_auth_str).decode("ascii")
        return self._decode_session(raw_auth_str)

    def _get_session_params(self):
        session_sources = [
            self._get_header_session_params,
            self._get_cookie_session_params,
        ]
        for token_source in session_sources:
            try:
                session_id, session_key = token_source()
                if session_id and session_key:
                    return session_id, session_key
            except:
                pass
        return None, None

    def get_current_user(self) -> Any:
        if self.user_id is None:
            session_id, session_key = self._get_session_params()
            if session_id and session_key:
                self.authenticate(session_id, session_key)
        return self.user_id

    def authenticate(self, session_id: int, session_key: str):
        if self.user_id is not None:
            # TODO print warning
            return
        with self.session.begin_nested():
            session: model.LoginSession = self.session.get(model.LoginSession, session_id)
            if session is None:
                raise ValueError("Invalid credentials")
            if not session.enabled:
                raise ValueError("Invalid credentials")
            now = datetime.utcnow()
            if session.expires_at < now:
                raise ValueError("Invalid credentials")
            if not pwd.compare(session_key, session.key):
                raise ValueError("Invalid credentials")
            session.expires_at = now + session.VALID_DURATION
            self.user_id = session.user_id
            self.login_session_id = session.id
        return self.user_id
