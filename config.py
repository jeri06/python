import os
import sys
databases = {
    "default": {
        "driver": "postgres",
        "user": "ioxywnihvztphy",
        "password": "1c191302812eeffae11e2a589088e327df391dc5d00140f43c3532c253397c0d",
        "host": "ec2-54-225-227-125.compute-1.amazonaws.com",
        "dbname": "dfne93uo3gnsjk",
        "port": 5432
    }
}
BASE_API = "/api/v1/"
settings = {
    "cookie_secret": "6ac74b05bd57a1f266a94ec5a929d0b92a9d9a6ec2b1457aa990dff101519a16bf7603759b2679f84b728667f7fc099c5"
                     "9fb6b244a9410993800174136b96fc8",
    "login_url": "/login",
    "debug": False,
    "static_path": os.path.join(os.path.dirname(__file__), "static"),
    "log_file_prefix": os.path.join(os.path.dirname(__file__), "logs/log"),
    "locale_path": os.path.join(os.path.dirname(__file__), "locale"),
    "tmp_path": os.path.join(os.path.dirname(__file__), "tmp"),
}

