import os

from aiohttp.web import Application, Response, MsgType, WebSocketResponse


class DataHanlder(object):
    def __init__(self):
        self.file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data.tsv')

    async def get(self, request):
        with open(self.file, 'rb') as fp:
            return Response(body=fp.read(), content_type='application/json')
