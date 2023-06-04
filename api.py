import cryptography.hazmat.primitives.serialization
import logging
import py_vapid
import tornado.escape
import typing

import auth
import model
import mywebpush

logger = logging.getLogger(__name__)


class Notification:
    DEFAULT_CHANNEL = "default"
    DEFAULT_LEVEL = 0

    channel: str
    level: int

    def __init__(self, channel: str|None = None, level: int|None = None):
        self.channel = channel or self.DEFAULT_CHANNEL
        self.level = level or self.DEFAULT_LEVEL


class ApiRequestHandler(auth.AuthRequestHandler):
    def ok(self):
        self.write(tornado.escape.json_encode({
            "ok": True,
        }))

    def write_error(self, status_code: int, **kwargs):
        exc_info = kwargs.get("exc_info")
        if exc_info is not None:
            exc_type, exc, traceback = exc_info
            self.finish(tornado.escape.json_encode({
                "error": str(exc),
            }))
        else:
            self.finish(tornado.escape.json_encode({
                "error": self._reason,
            }))

    def push(self, api_key: str, notification: Notification):
        api_key_obj = self.session.query(model.ApiKey) \
            .filter_by(key=api_key) \
            .one_or_none()
        if api_key_obj is None:
            raise ValueError("Invalid API key")
        if not api_key_obj.enabled:
            raise ValueError("API key disabled")
        user: model.User = api_key_obj.user
        if not user.enabled:
            raise ValueError("User disabled")
        channel_obj = self.session.query(model.Channel) \
            .filter_by(user_id=user.id) \
            .filter_by(name=notification.channel) \
            .one_or_none()
        if channel_obj is None:
            channel_obj = model.Channel.new(user, notification.channel)
            self.session.add(channel_obj)
        else:
            if channel_obj.min_level > int(notification.level):
                raise ValueError("Level too low")
        subscriptions: typing.Iterable[model.WebpushSubscription] = user.subscriptions
        for subscription in subscriptions:
            logger.debug("Pushing notification to %d", subscription.id)

    def push_and_finish(self, api_key: str, notification: Notification):
        self.push(api_key, notification)
        self.ok()
        self.finish()


class VapidRequestHandler(ApiRequestHandler):
    def get(self):
        raw_public_key = mywebpush.vapid.public_key.public_bytes(
            cryptography.hazmat.primitives.serialization.Encoding.X962,
            cryptography.hazmat.primitives.serialization.PublicFormat.UncompressedPoint,
        )
        public_key = py_vapid.b64urlencode(raw_public_key)
        self.write(tornado.escape.json_decode({
            "public_key": public_key,
        }))


class SubscribeRequestHandler(ApiRequestHandler):
    def post(self):
        all_info: dict = self.request.body.decode(self.request.body.decode("utf-8"))
        saved_info = {
            "endpoint": all_info["endpoint"],
            "keys": {
                "auth": self["keys"]["auth"],
                "p256dh": self["keys"]["p256dh"],
            },
        }
        already_existing = self.session.query(model.WebpushSubscription) \
            .filter_by(user_id=self.current_user) \
            .filter_by(info=tornado.escape.json_encode(saved_info)) \
            .one_or_none()
        if already_existing:
            raise ValueError("Already subscribed")
        user = self.session.get(model.User, self.current_user)
        subscription = model.WebpushSubscription.new(user, saved_info)
        self.session.add(subscription)
        self.session.commit()
        self.write(tornado.escape.json_encode(subscription))
        

    def delete(self):
        subscription_id = int(self.get_argument("id"))
        subscription = self.session.get(model.WebpushSubscription, subscription_id)
        self.session.delete(subscription)
        self.session.commit()
        self.ok()


class PushRequestHandler(ApiRequestHandler):
    def post(self):
        api_key = self.get_argument("key")
        notification = Notification(
            channel=self.get_argument("channel", None),
            level=int(self.get_argument("level", "0")),
        )
        self.push_and_finish(api_key, notification)
