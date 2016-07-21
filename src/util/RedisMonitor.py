#! /usr/bin/env python

try:
    from setting import settings
except:
    pass

from threading import Timer
import multiprocessing
import redis
import datetime
import threading
import traceback
import argparse
import time
import math
from util.Notice import EmailNotice

class InfoThread(threading.Thread):
    """Runs a thread to execute the INFO command against a given Redis server
    and store the resulting statistics in the configured stats provider.
    """

    def __init__(self, queue, server, port, password=None):
        """Initializes an InfoThread instance.

        Args:
            server (str): The host name of IP of the Redis server to monitor.
            port (int): The port number of the Redis server to monitor.

        Kwargs:
            password (str): The password to access the Redis server. \
                    Default: None
        """
        threading.Thread.__init__(self)
        self.result = queue
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
                redis_info["hit_rate"] = math.floor(key_hits / (key_hits + key_miss) * 100)

                self.result.put(redis_info)

                time.sleep(1)

            except Exception:
                tb = traceback.format_exc()
                print("==============================\n")
                print(datetime.datetime.now())
                print(tb)
                print("==============================\n")

class RedisMonitor(multiprocessing.Process):

    def __init__(self, duration, data_queue):
        multiprocessing.Process.__init__(self)
        self.threads = []
        self.active = True
        self.duration = duration
        self.data_queue = data_queue

    def main(self):
        """Monitors all redis servers defined in the config for a certain number
        of seconds.

        Args:
            duration (int): The number of seconds to monitor for.
        """
        redis_servers = settings.get("redis", [])

        for redis_server in redis_servers:

            redis_password = redis_server.get("password")
            info = InfoThread(self.data_queue, redis_server["server"], redis_server["port"], redis_password)
            self.threads.append(info)
            info.setDaemon(True)
            info.start()

        t = Timer(self.duration, self.stop)
        t.start()

        try:
            while self.active:
                pass
        except (KeyboardInterrupt, SystemExit):
            self.stop()
            t.cancel()

    def run(self):
        self.main()
        return

    def stop(self):
        """Stops the monitor and all associated threads.
        """
        # if args.quiet is False:
        #     print("shutting down...")
        for t in self.threads:
                t.stop()
        self.active = False


def run_process(result_queue):
    duration = 120
    monitor = RedisMonitor(duration, result_queue)
    monitor.start()
    return

if __name__ == '__main__':
    results = multiprocessing.Queue()
    duration = 120
    monitor = RedisMonitor(duration, results)
    monitor.run()
