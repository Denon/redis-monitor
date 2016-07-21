import traceback
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import  multiprocessing
from setting import settings

DEFAUTL_MONITOR_PARAM = {
    "used_memory_peak_human": "1K"
}


class EmailNotice(multiprocessing.Process):

    def __init__(self, data_queue, settings=None):
        self.queue = data_queue
        self.settings = settings or {}
        self.smtp_server = self.settings.get("email", {}).get("server", "")
        self.user = self.settings.get("email", {}).get("user", "")
        self.password = self.settings.get("email", {}).get("password", "")
        self.monitor_param = self.settings.get("monitor_param") or DEFAUTL_MONITOR_PARAM

    def connect(self):
        self.s = smtplib.SMTP_SSL(self.smtp_server, 465)
        self.s.login(self.user, self.password)

    def monitor(self, data):
        alert_items = []
        for key, value in self.monitor_param.items():
            if data.get(key) < value:
                alert_items.append(key)
                msg = "{}, expected:{}, current:{}".format(key, value, data.get(key))
        return '\n'.join(alert_items)

    def send(self, text):
        try:
            msg = MIMEText(text)
            msg['From'] = self.user
            msg['Subject'] = Header("redis-monitor", 'utf-8')
            err = self.s.sendmail("402139258@qq.com", "denonw@foxmail.com", msg.as_string())
            print(err)
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


if __name__ == "__main__":
    data_queue = multiprocessing.Queue()
    notice = EmailNotice(data_queue, settings=settings)
    data_queue.put({"used_memory_peak_human": "100K"})
    notice.run()