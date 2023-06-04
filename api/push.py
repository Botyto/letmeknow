import api.base


class PushRequestHandler(api.base.ApiRequestHandler):
    def post(self):
        api_key = self.get_argument("key")
        notification = api.base.Notification(
            channel=self.get_argument("channel", None),
            level=int(self.get_argument("level", "0")),
        )
        self.push_and_finish(api_key, notification)
