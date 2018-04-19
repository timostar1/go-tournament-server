# -*- coding: utf-8 -*-

import os
import xlrd

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
from tornado.options import define, options

import aiohttp
import motor.motor_asyncio
import os.path

DB_URL = "mongodb+srv://timostar:Upiter98!1wdb81e2q3r@cluster0-jmonj.mongodb.net/test"

define("port", default=8888, help="run on the given port", type=int)


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", RootHandler),
            (r"/api.*", APIHandler),
            (r"/auth/login", AuthLoginHandler),
            (r"/auth/create", AuthCreateHandler),
            (r"auth/logout", AuthLogoutHandler),
            (r"/players", PlayersHandler),
            (r"/download", DownloadHandler),
            (r"/profile.*", ProfileHandler),
        ]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            xsrf_cookies=True,
            # TODO
            cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
            login_url="/auth/login",
            static_path=os.path.join(os.path.dirname(__file__), "static"),
        )
        tornado.web.Application.__init__(self, handlers, **settings)

        # MongoDB
        self.client = motor.motor_asyncio.AsyncIOMotorClient(DB_URL)
        self.db = self.client.go_database


class BaseHandler(tornado.web.RequestHandler):
    # def get_current_user(self):
    #     user_id = self.get_secure_cookie("user")
    #     if not user_id: return None
    #     return self.backend.get_user_by_id(user_id)
    #
    # def get_user_locale(self):
    #     if "locale" not in self.current_user.prefs:
    #         # Use the Accept-Language header
    #         return None
    #     return self.current_user.prefs["locale"]

    @property
    def db(self):
        return self.application.db

    async def load_players(self):
        link = "http://gofederation.ru/players/?export=xlsx"
        async with aiohttp.ClientSession() as session:
            async with session.get(link) as resp:
                content = await resp.content.read()
                players = xlrd.open_workbook(file_contents=content).sheet_by_index(0)

        d = {"players": []}
        i = 0

        for row in players.get_rows():
            if i > 0:
                player = {"num": int(row[0].value),
                          "name": row[1].value,
                          "rating": int(row[2].value),
                          "r-delta": int(row[3].value),
                          "city": row[6].value, }
                d["players"].append(player)
            i += 1

        return d


class RootHandler(BaseHandler):
    async def get(self):
        # result = await self.db.users.find_one({"name": "test_name"})
        # self.write(str(result))
        self.render("index.html")


class AuthLoginHandler(BaseHandler):
    async def get(self):
        self.render("sign-in.html")


class AuthCreateHandler(BaseHandler):
    pass


class AuthLogoutHandler(BaseHandler):
    pass


class PlayersHandler(BaseHandler):
    async def get(self, *args, **kwargs):
        data = await self.load_players()
        self.render("players.html", players=data["players"])


class DownloadHandler(BaseHandler):
    pass


class APIHandler(BaseHandler):
    def __init__(self, *args, **kwargs):
        super(APIHandler, self).__init__(*args, **kwargs)

        self.api_functions = []
        self._find_api_functions()

    def api_function(func):
        async def wrapped(*args, **kwargs):
            await func(*args, **kwargs)
        wrapped.__name__ = func.__name__
        wrapped.__doc__ = "<api_function>"
        return wrapped

    def _find_api_functions(self):
        for attr_name in self.__dir__():
            try:
                attr = self.__getattribute__(attr_name)
            except AttributeError:
                continue
            if attr:
                if attr.__doc__ == "<api_function>":
                    self.api_functions.append(attr_name)

    async def get(self, *args, **kwargs):
        api_function = self.request.uri[5:]
        # print(self.request.arguments)
        if api_function == "":
            self.write("Go database API")
        else:
            func_name = api_function.split("?")[0]
            if func_name in self.api_functions:
                await self.__getattribute__(func_name)(**self.request.arguments)
            else:
                self.write(f"No function named {func_name}")

    @api_function
    async def test_api(self, *args, **kwargs):
        print(args, kwargs)
        self.write("API test passed!")

    @api_function
    async def players(self, *args, **kwargs):
        players = await self.load_players()
        content = "<table><tr><td>№</td><td>Имя</td><td>Рейтинг</td><td>Город</td></tr>"
        for player in players["players"]:
            s = (f"<tr><td>{player['num']}</td><td>{player['name']}</td><td>"
                 f"{player['rating']}</td><td>{player['city']}</td></tr>")
            content += s
        content += "</table>"
        html = f"<html><head></head><body>{content}</body></hmtl>"
        self.write(html)


class ProfileHandler(BaseHandler):
    pass


def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()