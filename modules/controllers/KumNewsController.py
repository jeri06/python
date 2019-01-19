import logging
import config
from tornado import gen
from tornado.web import asynchronous
from modules.services.KumNewServices import KumNewServices
from core.BaseController import BaseController


class KumNewsController(BaseController):
    def initialize(self):
        super().initialize()
        # noinspection PyAttributeOutsideInit
        self._service = KumNewServices(self.db_session)

    @gen.coroutine
    def post(self):
        response = {
            "success": True,
            "message": "Ok"
        }

        try:
            data = self.json_args
            # print(data)
            result = yield self._service.create(data)
            response["success"] = result["success"]
            response["message"] = "Create failed" if result.get("errors") else "Create Success"
            response["errors"] = result.get("errors")
            self.db_session.commit()
        except Exception as e:

            response["success"] = False
            response["message"] = str(e)
            logging.exception(e)
        self.write(response)
        self.finish()


urls = [
    (config.BASE_API + r"news", KumNewsController)
]
