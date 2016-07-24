import asyncio
import pathlib

import aiohttp_jinja2
import jinja2
from aiohttp import web

from web.handler.MainHandler import MainHandler
from web.handler.WebSocketHandler import RedisHanlder

PROJ_ROOT = pathlib.Path(__file__).parent.parent

async def get_app(loop, data_queue):
    app = web.Application()
    app['sockets'] = []
    mainhandler = MainHandler()
    redishandler = RedisHanlder(data_queue)
    app.router.add_route("GET", '/', mainhandler.get)
    app.router.add_route("*", '/data', redishandler.get)
    app.router.add_static('/static/',
                          path=str(PROJ_ROOT / 'static/css'),
                          name='static')
    aiohttp_jinja2.setup(
        app, loader=jinja2.PackageLoader('src', 'static'))
    srv = await loop.create_server(app.make_handler(), "0.0.0.0", port=9999)
    return srv

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_app(loop))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
