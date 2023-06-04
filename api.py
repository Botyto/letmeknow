import logging
import tornado.escape
import typing

import auth
import model

logger = logging.getLogger(__name__)


class ApiRequestHandler(auth.AuthRequestHandler):
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


class PushRequestHandler(ApiRequestHandler):
    def post(self):
        api_key = self.get_argument("key")
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
        channel = self.get_argument("channel", "default")
        channel_obj = self.session.query(model.Channel) \
            .filter_by(user_id=user.id) \
            .filter_by(name=channel) \
            .one_or_none()
        if channel_obj is None:
            channel_obj = model.Channel.new(user, channel)
            self.session.add(channel_obj)
        else:
            level = int(self.get_argument("level", "0"))
            if channel_obj.min_level > level:
                raise ValueError("Level too low")
        subscriptions: typing.Iterable[model.WebpushSubscription] = user.subscriptions
        for subscription in subscriptions:
            logger.debug("Pushing notification to %d", subscription.id)
        self.write(tornado.escape.json_encode({
            "ok": True,
        }))
