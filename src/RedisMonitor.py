#! /usr/bin/env python

try:
    from setting import settings
except:
    pass

import asyncio
import multiprocessing
import redis
import datetime
import threading
import traceback
import argparse
import time
import math
from redis.exceptions import ConnectionError
from util.Notice import run_notice
from web.app import get_app

class InfoThread(threading.Thread):
    """Runs a thread to execute the INFO command against a given Redis server.
    """

    def __init__(self, app_queue, notice_queue, server, port, password=None):
        """Initializes an InfoThread instance.
        """
        threading.Thread.__init__(self)
        self.app_queue = app_queue
        self.notice_queue = notice_queue
        self.server = server
        self.port = port
        self.password = password
        self.id = self.server + ":" + str(self.port)
        self._stop = threading.Event()

    def stop(self):
        """Stops the thread.
        """
        self._stop.set()

    def stopped(self):
        """Returns True if the thread is stopped, False otherwise.
        """
        return self._stop.is_set()

    def run(self):
        """Does all the work.
        """
        redis_client = redis.StrictRedis(host=self.server, port=self.port, db=0,
                                                 password=self.password)

        # process the results from redis
        while not self.stopped():
            try:
                redis_info = redis_client.info()
                key_hits = redis_info.get("keyspace_hits")
                key_miss = redis_info.get("keyspace_misses")
                if key_hits:
                    redis_info["hit_rate"] = math.floor(key_hits / (key_hits + key_miss) * 100)
                else:
                    redis_info["hit_rate"] = 0

            except ConnectionError:
                tb = traceback.format_exc()
                redis_info = {
                    "connection_error": True,
                    "error_message": tb
                }
            except Exception:
                tb = traceback.format_exc()
                # print("==============================\n")
                # print(datetime.datetime.now())
                # print(tb)
                # print("==============================\n")
                redis_info = {
                    "connection_error": True,
                    "error_message": tb
                }

            finally:
                self.app_queue.put(redis_info)
                self.notice_queue.put(redis_info)
                time.sleep(1)


class RedisMonitor(object):

    def __init__(self, app_queue, notice_queue):
        self.threads = []
        self.active = True
        self.app_queue = app_queue
        self.notice_queue = notice_queue

    def main(self):
        """Monitors all redis servers defined in the config for a certain number
        of seconds.

        Args:
            duration (int): The number of seconds to monitor for.
        """
        redis_servers = settings.get("redis", [])

        for redis_server in redis_servers:

            redis_password = redis_server.get("password")
            info = InfoThread(self.app_queue, self.notice_queue, redis_server["server"], redis_server["port"], redis_password)
            self.threads.append(info)
            info.setDaemon(True)
            info.start()

    def run(self):
        self.main()
        return

    def stop(self):
        """Stops the monitor and all associated threads.
        """
        # doesn't implement yet
        for t in self.threads:
            t.stop()
        self.active = False


def run_process(app_queue, notice_queue):
    monitor = RedisMonitor(app_queue, notice_queue)
    monitor.run()
    return

if __name__ == '__main__':
    try:
        app_queue = multiprocessing.Queue(2)
        notice_queue = multiprocessing.Queue()
        # start monitor
        run_process(app_queue, notice_queue)
        # start notice
        notice = run_notice(notice_queue)
        # start web server
        loop = asyncio.get_event_loop()
        loop.run_until_complete(get_app(loop, app_queue))
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        notice.join()
