import frontend.base
import model


class EditChannelRequestHandler(frontend.base.FrontendRequestHandler):
    def get(self):
        channel_name = self.get_argument("name")
        channel = self.session.query(model.Channel) \
            .filter_by(user_id=self.current_user) \
            .filter_by(name=channel_name) \
            .one_or_none()
        if channel is None:
            raise ValueError("Invalid channel")
        self.render("edit_channel.html", name=channel_name, channel=channel)

    def post(self):
        channel_name = self.get_argument("name")
        channel = self.session.query(model.Channel) \
            .filter_by(user_id=self.current_user) \
            .filter_by(name=channel_name) \
            .one_or_none()
        if channel is None:
            raise ValueError("Invalid channel")
        channel.enabled = self.get_argument("enabled") == "on"
        channel.min_level = int(self.get_argument("min_level"))
        self.session.commit()
        self.redirect("/")


class DeleteChannelRequestHandler(frontend.base.FrontendRequestHandler):
    def post(self):
        channel_name = self.get_argument("name")
        channel = self.session.query(model.Channel) \
            .filter_by(user_id=self.current_user) \
            .filter_by(name=channel_name) \
            .one_or_none()
        if channel is None:
            raise ValueError("Invalid channel")
        self.session.delete(channel)
        self.session.commit()
        self.redirect("/")
