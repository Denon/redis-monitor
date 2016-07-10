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
        with open(WS_FILE, 'rb') as fp:
            return Response(body=fp.read(), content_type='text/html')

    def post(self, request):
        pass
