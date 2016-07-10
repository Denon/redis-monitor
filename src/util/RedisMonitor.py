#! /usr/bin/env python

from setting_sample import settings
from threading import Timer
import multiprocessing
import redis
import datetime
import threading
import traceback
import argparse
import time


class DataAccess(object):
    @staticmethod
    def save_monitor_command(rid, timestamp, command, keyname, arguments):
        print(rid, timestamp, command, keyname, arguments)

    @staticmethod
    def save_memory_info(rid, current_time, used_memory, peak_memory):
        print(rid, current_time, used_memory, peak_memory)

    @staticmethod
    def save_info_command(rid, current_time, redis_info):
        print(rid, current_time, redis_info)


class Monitor(object):
    """Monitors a given Redis server using the MONITOR command.
    """

    def __init__(self, connection_pool):
        """Initializes the Monitor class.

        Args:
            connection_pool (redis.ConnectionPool): Connection pool for the \
                    Redis server to monitor.
        """
        self.connection_pool = connection_pool
        self.connection = None

    def __del__(self):
        try:
            self.reset()
        except:
            pass

    def reset(self):
        """If we have a connection, release it back to the connection pool.
        """
        if self.connection:
            self.connection_pool.release(self.connection)
            self.connection = None

    def monitor(self):
        """Kicks off the monitoring process and returns a generator to read the
        response stream.
        """
        if self.connection is None:
            self.connection = self.connection_pool.get_connection('monitor', None)
        self.connection.send_command("monitor")
        return self.listen()

    def parse_response(self):
        """Parses the most recent responses from the current connection.
        """
        return self.connection.read_response()

    def listen(self):
        """A generator which yields responses from the MONITOR command.
        """
        while True:
            yield self.parse_response()


class MonitorThread(threading.Thread):
    """Runs a thread to execute the MONITOR command against a given Redis server
    and store the resulting aggregated statistics in the configured stats
    provider.
    """

    def __init__(self, server, port, password=None):
        """Initializes a MontitorThread.

        Args:
            server (str): The host name or IP of the Redis server to monitor.
            port (int): The port to contact the Redis server on.

        Kwargs:
            password (str): The password to access the Redis host. Default: None
        """
        super(MonitorThread, self).__init__()
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
        """Runs the thread.
        """
        stats_provider = DataAccess()
        pool = redis.ConnectionPool(host=self.server, port=self.port, db=0,
                                    password=self.password)
        monitor = Monitor(pool)
        commands = monitor.monitor()

        for command in commands:
            try:
                parts = command.decode("utf-8").split(" ")

                if len(parts) == 1:
                    continue

                epoch = float(parts[0].strip())
                timestamp = datetime.datetime.fromtimestamp(epoch)

                # Strip '(db N)' and '[N x.x.x.x:xx]' out of the monitor str
                if (parts[1] == "(db") or (parts[1][0] == "["):
                    parts = [parts[0]] + parts[3:]

                command = parts[1].replace('"', '').upper()

                if len(parts) > 2:
                    keyname = parts[2].replace('"', '').strip()
                else:
                    keyname = None

                if len(parts) > 3:
                    # TODO: This is probably more efficient as a list
                    # comprehension wrapped in " ".join()
                    arguments = ""
                    for x in range(3, len(parts)):
                        arguments += " " + parts[x].replace('"', '')
                    arguments = arguments.strip()
                else:
                    arguments = None

                if not command == 'INFO' and not command == 'MONITOR':
                    stats_provider.save_monitor_command(self.id,
                                                        timestamp,
                                                        command,
                                                        str(keyname),
                                                        str(arguments))

            except Exception:
                tb = traceback.format_exc()
                print("==============================\n")
                print(datetime.datetime.now())
                print(tb)
                print(command)
                print("==============================\n")

            if self.stopped():
                break


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
        stats_provider = DataAccess()
        redis_client = redis.StrictRedis(host=self.server, port=self.port, db=0,
                                         password=self.password)

        # process the results from redis
        while not self.stopped():
            try:
                redis_info = redis_client.info()
                current_time = datetime.datetime.now()
                used_memory = int(redis_info['used_memory'])

                # used_memory_peak not available in older versions of redis
                try:
                    peak_memory = int(redis_info['used_memory_peak'])
                except:
                    peak_memory = used_memory

                # stats_provider.save_memory_info(self.id, current_time,
                #                                 used_memory, peak_memory)
                # stats_provider.save_info_command(self.id, current_time,
                #                                  redis_info)

                self.result.put(redis_info)

                # databases=[]
                # for key in sorted(redis_info.keys()):
                #     if key.startswith("db"):
                #         database = redis_info[key]
                #         database['name']=key
                #         databases.append(database)

                # expires=0
                # persists=0
                # for database in databases:
                #     expires+=database.get("expires")
                #     persists+=database.get("keys")-database.get("expires")

                # stats_provider.SaveKeysInfo(self.id, current_time, expires, persists)

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

            # monitor = MonitorThread(redis_server["server"], redis_server["port"], redis_password)
            # self.threads.append(monitor)
            # monitor.setDaemon(True)
            # monitor.start()

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
    # parser = argparse.ArgumentParser(description='Monitor redis.')
    # parser.add_argument('--duration',
    #                     type=int,
    #                     help="duration to run the monitor command (in seconds)",
    #                     required=True)
    # parser.add_argument('--quiet',
    #                     help="do  not write anything to standard output",
    #                     required=False,
    #                     action='store_true')
    # args = parser.parse_args()
    # duration = args.duration
    duration = 120
    monitor = RedisMonitor(duration, result_queue)
    monitor.start()
    return

if __name__ == '__main__':
    results = multiprocessing.Queue()
    # parser = argparse.ArgumentParser(description='Monitor redis.')
    # parser.add_argument('--duration',
    #                     type=int,
    #                     help="duration to run the monitor command (in seconds)",
    #                     required=True)
    # parser.add_argument('--quiet',
    #                     help="do  not write anything to standard output",
    #                     required=False,
    #                     action='store_true')
    # args = parser.parse_args()
    # duration = args.duration
    duration = 120
    monitor = RedisMonitor(duration, results)
    monitor.run()
