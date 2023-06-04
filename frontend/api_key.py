import frontend.base
import model


class NewApiKeyRequestHandler(frontend.base.FrontendRequestHandler):
    def post(self):
        user = self.session.get(model.User, self.current_user)
        api_key = model.ApiKey.new(user)
        self.session.add(api_key)
        self.session.commit()
        self.redirect("/")


class DeleteApiKeyRequestHandler(frontend.base.FrontendRequestHandler):
    def post(self):
        key = self.get_argument("key")
        api_key = self.session.query(model.ApiKey) \
            .filter_by(key=key) \
            .one_or_none()
        if api_key is None:
            raise ValueError("Invalid API key")
        self.session.delete(api_key)
        self.session.commit()
        self.redirect("/")
