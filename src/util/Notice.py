import threading
import re
import traceback
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from datetime import datetime
from datetime import timedelta
import  multiprocessing
from setting import settings

DEFAUTL_MONITOR_PARAM = {
    "used_memory_peak_human": "< 1K"
}


class EmailNotice(multiprocessing.Process):
    def __init__(self, data_queue, settings=None):
        super(EmailNotice, self).__init__()
        self.queue = data_queue
        self.settings = settings or {}
        self.smtp_server = self.settings.get("email", {}).get("server", "")
        self.user = self.settings.get("email", {}).get("user", "")
        self.password = self.settings.get("email", {}).get("password", "")
        self.monitor_param = self.settings.get("monitor_param") or DEFAUTL_MONITOR_PARAM
        self.senddelta = timedelta(hours=self.settings.get("email", {}).get("senddelta", ""))
        self.send_history = {}
        self._stop = threading.Event()

    def connect(self):
        try:
            self.s = smtplib.SMTP_SSL(self.smtp_server, 465)
            self.s.login(self.user, self.password)
        except smtplib.SMTPException:
            self.s = None

    def _time_check(self, key):
        now = datetime.now()
        if not self.send_history.get(key) or now - self.send_history.get(key) >= self.senddelta:
            return True
        else:
            return False

    def monitor(self, data):
        def _compare(v1, v2, operator):
            pattern = re.compile(r"\d*")
            v1 = pattern.match(v1).group()
            v2 = pattern.match(v2).group()
            if operator == "<" and v1 > v2:
                return True
            elif operator == ">" and v1 < v2:
                return True
            elif operator == "=" and v1 != v2:
                return True
            else:
                return False
        alert_messages = []
        if data.get("connection_error"):
            if self._time_check("connection_error"):
                now = datetime.now()
                msg = data.get("error_message")
                alert_messages.append(msg)
                self.send_history["connection_error"] = now
        else:
            for key, value in self.monitor_param.items():
                operator, alert_value = value.split(" ")
                if _compare(data.get(key), alert_value, operator):
                    now = datetime.now()
                    if self._time_check(key):
                        msg = "{}, expected:{}, current:{}".format(key, value, data.get(key))
                        alert_messages.append(msg)
                        self.send_history[key] = now
        return '\n'.join(alert_messages)

    def send(self, text):
        try:
            if self.s:
                msg = MIMEText(text)
                msg['From'] = self.user
                msg['Subject'] = Header("redis-monitor", 'utf-8')
                self.s.sendmail(self.user, self.settings.get("email", {}).get("to_addr"), msg.as_string())
            else:
                # todo add log later
                # print(text)
                pass
        except Exception:
            traceback.print_exc()

    def main_loop(self):
        while True:
            try:
                data = self.queue.get()
                alert_message = self.monitor(data)
                if alert_message:
                    self.send(alert_message)
            except Exception:
                traceback.print_exc()

    def run(self):
        self.connect()
        self.main_loop()
        return

def run_notice(data_queue):
    try:
        notice = EmailNotice(data_queue, settings=settings)
        notice.daemon = True
        notice.start()
        return notice
    except Exception:
        traceback.print_exc()

if __name__ == "__main__":
    data_queue = multiprocessing.Queue()
    notice = EmailNotice(data_queue, settings=settings)
    data_queue.put({"used_memory_peak_human": "100K"})
    data_queue.put({"used_memory_peak_human": "100K"})
    notice.start()