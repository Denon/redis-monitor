from aiohttp import web
from handler.MainHandler import MainHandler


def main():
    app = web.Application()
    mainhandler = MainHandler()
    app.router.add_route("GET", '/', mainhandler.get)
    return app

if __name__ == "__main__":
    app = main()
    web.run_app(app)
