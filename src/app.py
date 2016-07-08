import asyncio
import aiohttp_jinja2
import jinja2
from aiohttp import web
from handler.MainHandler import MainHandler
from handler.WebSocketHandler import websocket_handler


async def main(loop):
    app = web.Application()
    app['sockets'] = []
    mainhandler = MainHandler()
    app.router.add_route("GET", '/', mainhandler.get)
    app.router.add_route("*", '/test', websocket_handler)
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('./template'))
    srv = await loop.create_server(app.make_handler(), "0.0.0.0", port=9999)
    return srv

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
