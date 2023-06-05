import argparse
import json
import logging
import os
import tornado.ioloop
import tornado.web

import api.push
import api.webpush
import frontend.api_key
import frontend.auth
import frontend.base
import frontend.channel
import migrations
import mywebpush

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s - %(message)s')
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

env = {}
if os.path.isfile("env.json"):
    with open("env.json", "rt", encoding="utf-8") as fh:
        env = json.load(fh)

def run_migrations(action: str):
    manager = migrations.MigrationsManager(env)
    if action == "init":
        manager.init()
    elif action == "generate":
        title = None
        while not title:
            title = input("Enter the title of the migration: ")
        manager.generate(title)
    elif action == "update":
        manager.update()
    elif action == "uninstall":
        manager.uninstall()
    else:
        raise Exception(f"Unknown migrations action: {action}")

def start_server():
    mywebpush.load_vapid()
    handlers = [
        tornado.web.URLSpec("/api/push", api.push.PushRequestHandler, None, "api/push"),
        tornado.web.URLSpec("/api/vapid", api.webpush.VapidRequestHandler, None, "api/vapid"),
        tornado.web.URLSpec("/api/subscribe", api.webpush.SubscribeRequestHandler, None, "api/subscribe"),
        tornado.web.URLSpec("/", frontend.base.IndexRequestHandler, None, "index"),
        tornado.web.URLSpec("/auth/login", frontend.auth.LoginRequestHandler, None, "auth/login"),
        tornado.web.URLSpec("/auth/register", frontend.auth.RegisterRequestHandler, None, "auth/register"),
        tornado.web.URLSpec("/auth/logout", frontend.auth.LogoutRequestHandler, None, "auth/logout"),
        tornado.web.URLSpec("/api_key/new", frontend.api_key.NewApiKeyRequestHandler, None, "api_key/new"),
        tornado.web.URLSpec("/api_key/delete", frontend.api_key.DeleteApiKeyRequestHandler, None, "api_key/delete"),
        tornado.web.URLSpec("/channel/edit", frontend.channel.EditChannelRequestHandler, None, "channel/edit"),
        tornado.web.URLSpec("/channel/delete", frontend.channel.DeleteChannelRequestHandler, None, "channel/delete"),
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Backend server",
        description="Backend server")
    parser.add_argument("-m", "--migration", dest="migration",
        required=False, type=str,
        choices=["init", "generate", "update", "uninstall"])
    args = parser.parse_args()

    if args.migration:
        run_migrations(args.migration)
    else:
        start_server()
