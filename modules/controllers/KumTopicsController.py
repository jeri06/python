import logging
import config
from tornado import gen
from tornado.web import asynchronous
from modules.services.KumTopicsServices import KumTopicsServices

from core.BaseController import BaseController


class KumTopicsController(BaseController):
    def initialize(self):
        super().initialize()
        # noinspection PyAttributeOutsideInit
        self._service = KumTopicsServices(self.db_session)

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

    @gen.coroutine
    def get(self):
        response = {
            "success": True,
            "message": "Ok"
        }

        try:
            page = self.get_argument("page", 1, False)
            perPage = self.get_argument("limit", self.page_list_size(), False)
            filter = self.get_argument("filter", "[]", False)
            sort = self.get_argument("sort", "[]", False)


            rows, count = yield self._service.find(filter, int(page), int(perPage), sort)
            response["rows"] = rows
            response["total"] = count
        except Exception as e:

            response["success"] = False
            response["message"] = str(e)
            print(e)
            logging.exception(e)
        self.write(response)
        self.finish()

    @gen.coroutine
    def put(self):
        response = {
            "success": True,
            "message": "Ok"
        }

        try:
            data = self.json_args
            # print(data)
            result = yield self._service.update(data)
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

    @gen.coroutine
    def delete(self):
        response = {
            "success": True,
            "message": "Ok"
        }

        try:
            args = self.json_args
            count = 0
            result = {}
            errors = {}
            for data in args.get("data"):
                print(data.get("id"))
                result = yield self._service.delete(data.get("id"))
                if result.get("errors"):
                    errors.update(result.get("errors"))
                else:
                    count += 1
            response["success"] = result["success"]
            response["message"] = "{0} data deleted".format(count) if not errors else "One or more errors occured!"
            response["errors"] = errors
            self.db_session.commit()
        except Exception as e:
            response["success"] = False
            response["message"] = str(e)
            logging.exception(e)
        self.write(response)
        self.finish()


urls = [
    (config.BASE_API + r"topic", KumTopicsController)
]

