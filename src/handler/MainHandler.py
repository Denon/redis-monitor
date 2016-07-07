from aiohttp import web


class MainHandler:
    def __init__(self):
        pass

    async def get(self, request):
        return web.Response(body=b"Get all Redis Info")

    def post(self, request):
        pass
