import auth
import model


class FrontendRequestHandler(auth.AuthRequestHandler):
    def get_template_namespace(self):
        ns = super().get_template_namespace()
        user = self.session.get(model.User, self.current_user)
        ns.update({
            "user": user,
            "user_id": self.current_user,
        })
        return ns


class IndexRequestHandler(FrontendRequestHandler):
    def get(self):
        self.render("index.html")


class LoginRequestHandler(FrontendRequestHandler):
    def get(self):
        self.render("login.html")

    def post(self):
        manager = auth.AuthManager(self.session)
        username = self.get_argument("username")
        password = self.get_argument("password")
        session, session_key = manager.login(username, password)
        if session is None:
            raise ValueError("Invalid credentials")
        self.session.commit()
        self.set_secure_cookie("authorization", self._encode_session(session.id, session_key))
        self.redirect("/")


class RegisterRequestHandler(FrontendRequestHandler):
    def get(self):
        self.render("register.html")

    def post(self):
        manager = auth.AuthManager(self.session)
        username = self.get_argument("username")
        password = self.get_argument("password")
        user = manager.register(username, password)
        if user is None:
            raise ValueError("Something went wrong")
        self.session.commit()
        session, session_key = manager.login(username, password)
        if session is None:
            raise ValueError("Something went wrong - try logging in again")
        self.session.commit()
        self.set_secure_cookie("authorization", self._encode_session(session.id, session_key))
        self.redirect("/")


class LogoutRequestHandler(FrontendRequestHandler):
    def get(self):
        self.get_current_user()
        manager = auth.AuthManager(self.session)
        manager.logout(self.login_session_id)
        self.clear_cookie("authorization")
        self.redirect("/")


class NewApiKeyRequestHandler(FrontendRequestHandler):
    def post(self):
        user = self.session.get(model.User, self.current_user)
        api_key = model.ApiKey.new(user)
        self.session.add(api_key)
        self.session.commit()
        self.redirect("/")
