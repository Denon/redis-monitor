import jinja2
import aiohttp_jinja2
from aiohttp import web
import os
from aiohttp.web import Application, Response, MsgType, WebSocketResponse

WS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'template/index.html')

"""
copy from https://github.com/KeepSafe/aiohttp/blob/master/examples/web_ws.py
"""

class MainHandler:
    def __init__(self):
        pass

    async def get(self, request):
        resp = WebSocketResponse()
        ok, protocol = resp.can_prepare(request)
        if not ok:
            with open(WS_FILE, 'rb') as fp:
                return Response(body=fp.read(), content_type='text/html')

        await resp.prepare(request)
        print('Someone joined.')
        for ws in request.app['sockets']:
            ws.send_str('Someone joined')
        request.app['sockets'].append(resp)

        while True:
            msg = await resp.receive()

            if msg.tp == MsgType.text:
                for ws in request.app['sockets']:
                    if ws is not resp:
                        ws.send_str(msg.data)
            else:
                break

        request.app['sockets'].remove(resp)
        print('Someone disconnected.')
        for ws in request.app['sockets']:
            ws.send_str('Someone disconnected.')
        return resp

    def post(self, request):
        pass
