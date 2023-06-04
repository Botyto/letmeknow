from datetime import datetime, timedelta
import random
import sqlalchemy
import sqlalchemy.orm
import typing

import db
import password as pwd


class User(db.Model):
    __tablename__ = "User"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True, nullable=False)
    enabled = sqlalchemy.Column(sqlalchemy.Boolean, default=True, nullable=False)
    username = sqlalchemy.Column(sqlalchemy.String(128), index=True, unique=True)
    password = sqlalchemy.Column(sqlalchemy.Text, nullable=False)

    @classmethod
    def new(cls, username: str, password: str) -> "User":
        pwd.validate(password)
        user = cls(
            username=username,
            password=pwd.hash(password),
        )
        return user


class ApiKey(db.Model):
    __tablename__ = "ApiKey"
    key = sqlalchemy.Column(sqlalchemy.String(32), primary_key=True, nullable=False)
    enabled = sqlalchemy.Column(sqlalchemy.Boolean, default=True, nullable=False)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("User.id", onupdate="CASCADE", ondelete="CASCADE"))
    user = sqlalchemy.orm.relationship("User", backref=sqlalchemy.orm.backref("api_keys", uselist=True), lazy="joined")

    KEY_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._~"

    @classmethod
    def new(cls, user: User) -> typing.Tuple["LoginSession", str]:
        key = "".join(random.choices(cls.KEY_CHARS, k=32))
        api_key = cls(
            key=key,
            user_id=user.id,
            user=user,
        )
        return api_key


class LoginSession(db.Model):
    __tablename__ = "LoginSession"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True, nullable=False)
    enabled = sqlalchemy.Column(sqlalchemy.Boolean, default=True, nullable=False)
    expires_at = sqlalchemy.Column(sqlalchemy.DateTime, nullable=False)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("User.id", onupdate="CASCADE", ondelete="CASCADE"))
    user = sqlalchemy.orm.relationship("User", backref=sqlalchemy.orm.backref("logins", uselist=True), lazy="joined")
    key = sqlalchemy.Column(sqlalchemy.Text, nullable=False)

    VALID_DURATION = timedelta(days=30)
    KEY_CHARS = ApiKey.KEY_CHARS

    @classmethod
    def new(cls, user: User) -> typing.Tuple["LoginSession", str]:
        key = "".join(random.choices(cls.KEY_CHARS, k=32))
        session = cls(
            user_id=user.id,
            user=user,
            key=pwd.hash(key),
            expires_at=datetime.utcnow() + cls.VALID_DURATION,
        )
        return session, key


class WebpushSubscription(db.Model):
    __tablename__ = "WebpushSubscription"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True, nullable=False)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("User.id", onupdate="CASCADE", ondelete="CASCADE"))
    user = sqlalchemy.orm.relationship("User", backref=sqlalchemy.orm.backref("subscriptions", uselist=True), lazy="joined")
    info = sqlalchemy.Column(sqlalchemy.JSON, nullable=False)

    @classmethod
    def new(cls, user: User, info: dict) -> "WebpushSubscription":
        subscription = cls(
            user_id=user.id,
            user=user,
            info=info,
        )
        return subscription


class Channel(db.Model):
    __tablename__ = "Channel"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True, nullable=False)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("User.id", onupdate="CASCADE", ondelete="CASCADE"))
    user = sqlalchemy.orm.relationship("User", backref=sqlalchemy.orm.backref("channels", uselist=True), lazy="joined")
    enabled = sqlalchemy.Column(sqlalchemy.Boolean, default=True, nullable=False)
    name = sqlalchemy.Column(sqlalchemy.String(128), index=True, nullable=False)
    min_level = sqlalchemy.Column(sqlalchemy.Integer, default=0, nullable=False)

    @classmethod
    def new(cls, user: User, name: str):
        return cls(
            user_id=user.id,
            user=user,
            name=name,
        )
