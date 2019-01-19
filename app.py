import tornado.ioloop
from modules.urls import app
from config import settings
import tornado.httpserver
from tornado.options import define, options
import os
def run_dev(ports):
    for p in ports:
        app.listen(p)
        print("> App listen on port " + str(p))
        print("> Server run forever")
    tornado.ioloop.IOLoop.current().start()


def run_mp_support(port):
    server = tornado.httpserver.HTTPServer(app)
    server.bind(port)
    server.start(0)  # forks one process per cpu
    print("> App listen on port " + str(port))
    print("> Server run forever")
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    # tornado.locale.load_translations(settings['locale_path'])
    #port = os.environ['PORT']
    ports = [os.environ['PORT']]
    print(ports)
    run_dev(ports)


