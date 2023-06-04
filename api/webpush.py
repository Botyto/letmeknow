import cryptography.hazmat.primitives.serialization
import py_vapid
import tornado.escape

import api.base
import model
import mywebpush


class VapidRequestHandler(api.base.ApiRequestHandler):
    def get(self):
        raw_public_key = mywebpush.vapid.public_key.public_bytes(
            cryptography.hazmat.primitives.serialization.Encoding.X962,
            cryptography.hazmat.primitives.serialization.PublicFormat.UncompressedPoint,
        )
        public_key = py_vapid.b64urlencode(raw_public_key)
        self.write(tornado.escape.json_decode({
            "public_key": public_key,
        }))


class SubscribeRequestHandler(api.base.ApiRequestHandler):
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