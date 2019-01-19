'''
Created on Apr 12, 2016

@author: kakan
'''
from tornado.web import Application
from config import settings
from tornado.options import options
import tornado.log

class StartUp():
    
    def __init__(self):
        self._app = None
        self._settings = settings
    
    def create_app(self, urls):
        for url in urls:
            print("=>" + url[0])

        print(self._settings)
        self._set_up_log()
        self._app = Application(urls, self._settings)
        return self._app
    
    
    def _set_up_log(self):
        options = tornado.options.options
        options.log_file_prefix = settings["log_file_prefix"]
        options.logging = "error"
        options.log_rotate_mode = "time"
        options.log_rotate_when = "S"
        options.log_rotate_interval = 30
        options.log_file_num_backups = 6
        tornado.log.enable_pretty_logging(options)