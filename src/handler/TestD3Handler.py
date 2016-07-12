import os

from aiohttp.web import Application, Response, MsgType, WebSocketResponse


class TestD3Hanlder(object):
    def __init__(self):
        self.file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'template/d3.html')

    async def get(self, request):
        with open(self.file, 'rb') as fp:
            return Response(body=fp.read(), content_type='text/html')
