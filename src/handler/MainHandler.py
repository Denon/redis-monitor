import jinja2
import aiohttp_jinja2
from aiohttp import web
import os
from aiohttp.web import Application, Response, MsgType, WebSocketResponse

WS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static/index.html')

"""
copy from https://github.com/KeepSafe/aiohttp/blob/master/examples/web_ws.py
"""

class MainHandler:
    def __init__(self):
        pass

    @aiohttp_jinja2.template('index.html')
    async def get(self, request):

        return {}

    def post(self, request):
        pass
