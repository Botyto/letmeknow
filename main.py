import logging
import tornado.ioloop
import tornado.web

import api
import db
import frontend

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s - %(message)s')
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

if __name__ == "__main__":
    logger.info("Setting up SQLite database")
    db.Model.metadata.create_all(db.engine)
    handlers = [
        tornado.web.URLSpec("/api/push", api.PushRequestHandler, None, "api/push"),
        tornado.web.URLSpec("/", frontend.IndexRequestHandler, None, "index"),
        tornado.web.URLSpec("/login", frontend.LoginRequestHandler, None, "login"),
        tornado.web.URLSpec("/register", frontend.RegisterRequestHandler, None, "register"),
        tornado.web.URLSpec("/logout", frontend.LogoutRequestHandler, None, "logout"),
        tornado.web.URLSpec("/new_api_key", frontend.NewApiKeyRequestHandler, None, "new_api_key"),
    ]
    webapp = tornado.web.Application(
        handlers,
        template_path="templates",
        static_path="static",
        compiled_template_cache=True,
        static_hash_cache=True,
        compress_response=True,
        cookie_secret="test",
    )
    port = 80
    webapp.listen(port)
    logger.info("Listening on port %d", port)
    loop = tornado.ioloop.IOLoop.current()
    loop.start()
