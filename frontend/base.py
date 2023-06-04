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
