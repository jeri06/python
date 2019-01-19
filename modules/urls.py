# from tornado.web import StaticFileHandler
import os

from core.Starter import StartUp
from core.url import UrlCollector

# register url here
urlreg = UrlCollector().instance()
for root, dirs, files in os.walk(os.path.dirname(__file__)):
    if root.endswith('controllers'):
        pardir = root.split(os.sep)[-2]
        for file in files:
            if not file.startswith('__'):
                try:
                    filename = file.split('.')[0]
                    imported_name = "{0}_url".format(filename.lower())
                    import_string = "from modules.controllers.{1} import urls as {2}".format(pardir, filename,imported_name)
                    print("TES" + import_string)
                    exec(import_string)

                    urlreg.collect(locals()[imported_name])
                except (ImportError, NotImplementedError) as e:
                    print(e)
urls = urlreg.list_url

for url in urls:
    print(url[0])

applicationStartup = StartUp()
app = applicationStartup.create_app(urls)
