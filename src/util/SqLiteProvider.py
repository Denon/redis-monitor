import sqlite3
import contextlib
from datetime import datetime
from setting import settings


class SqLiteProvider(object):
    def __init__(self):
        sqlite_setting = settings.get("sqlite")
        self.location = sqlite_setting.get('path', 'db/redislive.sqlite')
        self.conn = sqlite3.connect(self.location)
        self.retries = 10

    def _execute(self, sql, *args):
        with contextlib.closing(self.conn.cursor()) as cursor:
            try:
                cursor.execute(sql, args)
                self.conn.commit()
            except Exception as e:
                pass

    def save_info(self, info):
        sql = """
        INSERT INTO info (info, datetime) VALUES (?, ?)
        """
        now = str(datetime.now())
        self._execute(sql, info, now)

    def get_info(self):
        pass

if __name__ == "__main__":
    provider = SqLiteProvider()
    info = "123"
    provider.save_info(info)
