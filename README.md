# redis-monitor

![Python 3.5](https://img.shields.io/badge/python-3.5-blue.svg)

Redis-Monitor is a tool for monitoring your redis server. I use command `info`([see this](http://redis.io/commands/INFO)), because it doesn't seriously affects performance compare to `monitor` command. 

Features:
* show basic stat if dashboard
* send notice email with abnormal data

# preview
![preview](https://raw.githubusercontent.com/Denon/redis-monitor/master/src/web/static/preview.png)


# how to run
1. install requirements
2. cp setting_sample.py setting.py
3. start RedisMonitor.py
