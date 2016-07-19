import aiohttp
import json
from aiohttp.web import Application, Response, MsgType, WebSocketResponse


class RedisHanlder(object):
    def __init__(self, queue):
        self.queue = queue

    async def get(self, request):
        resp = WebSocketResponse()

        await resp.prepare(request)
        print('Someone joined.')
        for ws in request.app['sockets']:
            ws.send_str('Someone joined')
        request.app['sockets'].append(resp)

        while True:
            msg = await resp.receive()

            if msg.tp == MsgType.text:
                for ws in request.app['sockets']:
                    redis_info = self.queue.get()
                    ws.send_str(json.dumps(redis_info))
            else:
                break

        request.app['sockets'].remove(resp)
        print('Someone disconnected.')
        for ws in request.app['sockets']:
            ws.send_str('Someone disconnected.')
        return resp
