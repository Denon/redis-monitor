"""
redis-monitor setting

in redis:
    set redis server which you want to monitor
in monitor_param:
    support operator include: '<', '>', '='
    example:
    {
        "used_memory_peak_human": "< 1K"
    }
in email:
    server: smtp server
    user: smtp username and from_addr
    password: smtp password
    to_addr:
    senddelta: send time delta (hours)
"""

settings = {
    "redis": [
        {
            "server": "0.0.0.0",
            "password": "",
            "port": 6379
        }
    ],
    "monitor_param": {

    },
    "email": {
        "server": "",
        "user": "",
        "password": "",
        "to_addr": "",
        "senddelta": 1
    }
}