import os
import logging
import config
import traceback
import simplejson as json

from tornado import httpclient
from tornado_cors import CorsMixin
# from tornado_cros import CorsMixin
from tornado.httpclient import AsyncHTTPClient, httputil
from tornado import gen
from tornado.web import asynchronous

from db import SessionFactory
from core.RequestHandler import RequestHandler
# from libs.jwt import JWTAuth


class BaseController(CorsMixin, RequestHandler):
    # Value for the Access-Control-Allow-Origin header.
    # Default: None (no header).
    CORS_ORIGIN = '*'

    # Value for the Access-Control-Allow-Headers header.
    # Default: None (no header).
    CORS_HEADERS = 'Content-Type'

    # Value for the Access-Control-Allow-Methods header.
    # Default: Methods defined in handler class.
    # None means n\o header.
    CORS_METHODS = '*'

    # Value for the Access-Control-Allow-Credentials header.
    # Default: None (no header).
    # None means no header.
    CORS_CREDENTIALS = True

    # Value for the Access-Control-Max-Age header.
    # Default: 86400.
    # None means no header.
    CORS_MAX_AGE = 21600

    # Value for the Access-Control-Expose-Headers header.
    # Default: None
    CORS_EXPOSE_HEADERS = 'x-requested-with,Content-Type,Authorization'

    def initialize(self):
        self.current_roles = None
        try:
            self.db_session = SessionFactory.instance(True).get_session()
        except Exception:
            self.db_session = None

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header('Access-Control-Allow-Credentials', "true")
        self.set_header("Access-Control-Allow-Headers", "X-Requested-With,Content-Type,Authorization")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, PUT, OPTIONS, DELETE')
        self.set_header("Access-Control-Max-Age", 3600)

    def write_error(self, status_code, **kwargs):
        if self.db_session:
            self.db_session.close()
        RequestHandler.write_error(status_code=status_code, **kwargs)

    def finish(self, chunk=None):
        try:
            if self.db_session:
                self.db_session.close()
            RequestHandler.finish(self, chunk=chunk)
        except Exception as e:
            print(e)

    def write_error_no_db_session(self, status_code, **kwargs):
        if self.settings.get("serve_traceback") and "exc_info" in kwargs:
            # in debug mode, try to send a traceback
            self.set_header('Content-Type', 'text/plain')
            for line in traceback.format_exception(*kwargs["exc_info"]):
                self.write(line)
            self.finish_no_db_session()
        else:
            self.finish_no_db_session("<html><title>%(code)d: %(message)s</title>"
                                      "<body>%(code)d: %(message)s</body></html>" % {
                                          "code": status_code,
                                          "message": self._reason,
                                      })

    def finish_no_db_session(self, chunk=None):
        if self._finished:
            raise RuntimeError("finish() called twice")

        if chunk is not None:
            self.write(chunk)

        # Automatically support ETags and add the Content-Length header if
        # we have not flushed any content yet.
        if not self._headers_written:
            if (self._status_code == 200 and
                    self.request.method in ("GET", "HEAD") and
                    "Etag" not in self._headers):
                self.set_etag_header()
                if self.check_etag_header():
                    self._write_buffer = []
                    self.set_status(304)
            if self._status_code in (204, 304):
                assert not self._write_buffer, "Cannot send body with %s" % self._status_code
                self._clear_headers_for_304()
            elif "Content-Length" not in self._headers:
                content_length = sum(len(part) for part in self._write_buffer)
                self.set_header("Content-Length", content_length)

        if hasattr(self.request, "connection"):
            # Now that the request is finished, clear the callback we
            # set on the HTTPConnection (which would otherwise prevent the
            # garbage collection of the RequestHandler when there
            # are keepalive connections)
            self.request.connection.set_close_callback(None)

        self.flush(include_footers=True)
        self.request.finish()
        self._log()
        self._finished = True
        self.on_finish()
        self._break_cycles()

    def options(self, *args, **kwargs):
        self.write({"success": True})

    # @staticmethod
    # def get_sys_user(token, username):
    #     http_client = httpclient.HTTPClient()
    #     try:
    #         auth_header = token
    #         headers = {"Accept": "*/*", "Content-Type": "application/json; charset=UTF-8", "Authorization": auth_header}
    #         params = {'page': 1, 'limit': 100}
    #
    #         filters = [
    #             {
    #                 'property': "username",
    #                 'value': username,
    #                 'operator': "="
    #             }
    #         ]
    #         params['filter'] = json.dumps(filters)
    #         params['sort'] = "[]"
    #
    #         str_params = ""
    #         if params:
    #             str_params = "?" + httputil.urlencode(params).encode().decode("utf-8")
    #         url = config.ADMIN_API_URL + config.BASE_API + "/{0}".format("user") + str_params
    #         response = http_client.fetch(url, method="GET", headers=headers)
    #         data = json.loads(response.body.decode("UTF-8"))
    #         return data.get("rows")
    #     except httpclient.HTTPError as e:
    #         logging.exception(e)
    #     except Exception as e:
    #         logging.exception(e)
    #     http_client.close()

    # def get_token_payload(self, key):
    #     jwt_auth = JWTAuth(self)
    #     token_data = jwt_auth.check_authentication()
    #     return token_data.get(key) if token_data else False
    #
    # def get_current_user(self):
    #     jwt_auth = JWTAuth(self)
    #     token_data = jwt_auth.check_authentication()
    #     self.current_user = token_data.get("user") if token_data else False
    #     return self.current_user
    #
    # def get_current_user_id(self):
    #     jwtAuth = JWTAuth(self)
    #     token_data = jwtAuth.check_authentication()
    #     self.current_user = token_data.get("user_id") if token_data else False
    #     return self.current_user

    def get_template(self, template):
        return os.path.join(self.get_static_path(), template)

    @staticmethod
    def get_static_path():
        return config.settings.get("static_path")

    @staticmethod
    def page_list_size():
        return 100

    def prepare(self):
        if self.request.headers.get("Content-Type") is not None and self.request.headers["Content-Type"].startswith(
                "application/json"):
            body = self.request.body.decode('ascii')
            try:
                self.json_args = json.loads(body)
            except Exception as e:
                logging.exception(e)
        else:
            self.json_args = None


class ProxyController(BaseController):
    def initialize(self):
        self._service = None

    @asynchronous
    @gen.engine
    def get(self):
        try:
            http_client = AsyncHTTPClient()
            auth_header = self.request.headers.get('Authorization')
            headers = {"Accept": "*/*", "Content-Type": "application/json; charset=UTF-8", "Authorization": auth_header}
            params = {
                'query': self.get_argument("query", "", False),
                'page': self.get_argument("page", 1, False),
                'limit': self.get_argument("limit", self.page_list_size(), False),
                'filter': self.get_argument("filter", "[]", False),
                'sort': self.get_argument("sort", "[]", False)
            }
            str_params = ""
            if params:
                str_params = "?" + httputil.urlencode(params).encode().decode("utf-8")
            url = config.ADMIN_API_URL + config.BASE_API + "{0}".format(self._service) + str_params
            print(url)

            def request_callback(respons):
                body = respons.body.decode("UTF-8")
                json_response = json.loads(body)
                print(json_response)
                self.write(json_response)
                # self.finish_no_db_session()

            yield http_client.fetch(url, method="GET", callback=request_callback, headers=headers)

        except Exception as e:
            response = {
                "success": False,
                "message": "Something went wrong."
            }
            logging.exception(e)
            self.write(response)
        finally:
            self.finish_no_db_session()

    @asynchronous
    @gen.engine
    def post(self):
        try:
            body = json.dumps(self.json_args)
            auth_header = self.request.headers.get('Authorization')
            headers = {"Accept": "*/*", "Content-Type": "application/json; charset=UTF-8", "Authorization": auth_header}
            http_client = AsyncHTTPClient()
            url = config.ADMIN_API_URL + config.BASE_API + "{0}".format(self._service)
            response = yield http_client.fetch(url, method="POST", headers=headers, body=body)
            body = response.body.decode("utf-8")
            json_response = json.loads(body)
            self.write(json_response)
        except Exception as e:
            response = {
                "success": False,
                "message": "Something went wrong."
            }
            logging.exception(e)
            self.write(response)
        self.finish_no_db_session()

    @asynchronous
    @gen.engine
    def put(self):
        try:
            body = json.dumps(self.json_args)
            auth_header = self.request.headers.get('Authorization')
            headers = {"Accept": "*/*", "Content-Type": "application/json; charset=UTF-8", "Authorization": auth_header}
            http_client = AsyncHTTPClient()
            url = config.ADMIN_API_URL + config.BASE_API + "{0}".format(self._service)
            response = yield http_client.fetch(url, method="PUT", headers=headers, body=body)
            body = response.body.decode("utf-8")
            json_response = json.loads(body)
            self.write(json_response)
        except Exception as e:
            response = {
                "success": False,
                "message": "Something went wrong."
            }
            logging.exception(e)
            self.write(response)
        self.finish_no_db_session()

    @asynchronous
    @gen.engine
    def delete(self):
        try:
            body = json.dumps(self.json_args)
            auth_header = self.request.headers.get('Authorization')
            headers = {"Accept": "*/*", "Content-Type": "application/json; charset=UTF-8", "Authorization": auth_header}
            http_client = AsyncHTTPClient()
            url = config.ADMIN_API_URL + config.BASE_API + "{0}".format(self._service)
            response = yield http_client.fetch(url, method="DELETE", headers=headers, body=body)
            body = response.body.decode("utf-8")
            json_response = json.loads(body)
            self.write(json_response)
        except Exception as e:
            response = {
                "success": False,
                "message": "Something went wrong."
            }
            logging.exception(e)
            self.write(response)
        self.finish_no_db_session()

    def options(self):
        response = {
            "success": True,
            "message": "Ok"
        }
        self.write(response)
        self.finish_no_db_session()


class ProxyDetailController(BaseController):
    def initialize(self):
        self._service = None

    def options(self, id):
        self.write({"success": True, "id": id})
        self.finish_no_db_session()

    @asynchronous
    @gen.engine
    def get(self, id):
        try:
            http_client = AsyncHTTPClient()
            url = config.ADMIN_API_URL + config.BASE_API + "{0}/".format(self._service) + id
            auth_header = self.request.headers.get('Authorization')
            headers = {"Accept": "*/*", "Content-Type": "application/json; charset=UTF-8", "Authorization": auth_header}
            response = yield http_client.fetch(url, method="GET", headers=headers)
            body = response.body.decode("utf-8")
            json_response = json.loads(body)
            self.write(json_response)
        except Exception as e:
            response = {
                "success": False,
                "message": "Something went wrong."
            }
            logging.exception(e)
            self.write(response)
        self.finish_no_db_session()

    @asynchronous
    @gen.engine
    def delete(self, id):
        try:
            http_client = AsyncHTTPClient()
            url = config.ADMIN_API_URL + config.BASE_API + "{0}/".format(self._service) + id
            auth_header = self.request.headers.get('Authorization')
            headers = {"Accept": "*/*", "Content-Type": "application/json; charset=UTF-8", "Authorization": auth_header}
            response = yield http_client.fetch(url, method="DELETE", headers=headers)
            body = response.body.decode("utf-8")
            json_response = json.loads(body)
            self.write(json_response)
        except Exception as e:
            response = {
                "success": False,
                "message": "Something went wrong."
            }
            logging.exception(e)
            self.write(response)
        self.finish_no_db_session()


class ProxyPublicController(BaseController):
    def initialize(self):
        self._service = None

    @asynchronous
    @gen.engine
    def get(self):
        try:
            http_client = AsyncHTTPClient()
            headers = {
                "Content-Type": "application/json; charset=UTF-8",
            }
            params = {
                'page': self.get_argument("page", 1, False),
                'limit': self.get_argument("limit", self.page_list_size(), False),
                'filter': self.get_argument("filter", "[]", False),
                'sort': self.get_argument("sort", "[]", False)
            }
            str_params = ""
            if params:
                str_params = "?" + httputil.urlencode(params).encode().decode("utf-8")
            url = config.ADMIN_API_URL + config.BASE_API + "{0}".format(self._service) + str_params

            def request_callback(respons):
                body = respons.body.decode("UTF-8")
                json_response = json.loads(body)
                self.write(json_response)
                self.finish_no_db_session()

            http_client.fetch(url, method="GET", callback=request_callback, headers=headers)

        except Exception as e:
            response = {
                "success": False,
                "message": "Something went wrong."
            }
            logging.exception(e)
            self.write(response)
            self.finish_no_db_session()

    @asynchronous
    @gen.engine
    def post(self):
        try:
            body = json.dumps(self.json_args)
            headers = {"Content-Type": "application/json; charset=UTF-8"}
            http_client = AsyncHTTPClient()
            url = config.ADMIN_API_URL + config.BASE_API + "{0}".format(self._service)
            response = yield http_client.fetch(url, method="POST", headers=headers, body=body)
            body = response.body.decode("utf-8")
            json_response = json.loads(body)
            self.write(json_response)
        except Exception as e:
            response = {
                "success": False,
                "message": "Something went wrong."
            }
            logging.exception(e)
            self.write(response)
        self.finish_no_db_session()

    @asynchronous
    @gen.engine
    def put(self):
        try:
            body = json.dumps(self.json_args)
            headers = {"Content-Type": "application/json; charset=UTF-8"}
            http_client = AsyncHTTPClient()
            url = config.ADMIN_API_URL + config.BASE_API + "{0}".format(self._service)
            response = yield http_client.fetch(url, method="PUT", headers=headers, body=body)
            body = response.body.decode("utf-8")
            json_response = json.loads(body)
            self.write(json_response)
        except Exception as e:
            response = {
                "success": False,
                "message": "Something went wrong."
            }
            logging.exception(e)
            self.write(response)
        self.finish_no_db_session()

    @asynchronous
    @gen.engine
    def delete(self):
        try:
            body = json.dumps(self.json_args)
            headers = {"Content-Type": "application/json; charset=UTF-8"}
            http_client = AsyncHTTPClient()
            url = config.ADMIN_API_URL + config.BASE_API + "{0}".format(self._service)
            response = yield http_client.fetch(url, method="DELETE", headers=headers, body=body)
            body = response.body.decode("utf-8")
            json_response = json.loads(body)
            self.write(json_response)
        except Exception as e:
            response = {
                "success": False,
                "message": "Something went wrong."
            }
            logging.exception(e)
            self.write(response)
        self.finish_no_db_session()

    def options(self):
        response = {
            "success": True,
            "message": "Ok"
        }
        self.write(response)
        self.finish_no_db_session()


class ProxyDetailPublicController(BaseController):
    def initialize(self):
        self._service = None

    def options(self, id):
        self.write({"success": True, "id": id})
        self.finish_no_db_session()

    @asynchronous
    @gen.engine
    def get(self, id):
        try:
            http_client = AsyncHTTPClient()
            url = config.ADMIN_API_URL + config.BASE_API + "{0}/".format(self._service) + id
            headers = {"Content-Type": "application/json; charset=UTF-8"}
            response = yield http_client.fetch(url, method="GET", headers=headers)
            body = response.body.decode("utf-8")
            json_response = json.loads(body)
            self.write(json_response)
        except Exception as e:
            response = {
                "success": False,
                "message": "Something went wrong."
            }
            logging.exception(e)
            self.write(response)
        self.finish_no_db_session()

    @asynchronous
    @gen.engine
    def delete(self, id):
        try:
            http_client = AsyncHTTPClient()
            url = config.ADMIN_API_URL + config.BASE_API + "{0}/".format(self._service) + id
            headers = {"Content-Type": "application/json; charset=UTF-8"}
            response = yield http_client.fetch(url, method="DELETE", headers=headers)
            body = response.body.decode("utf-8")
            json_response = json.loads(body)
            self.write(json_response)
        except Exception as e:
            response = {
                "success": False,
                "message": "Something went wrong."
            }
            logging.exception(e)
            self.write(response)
        self.finish_no_db_session()


class ProxyShortDetailPublicController(BaseController):
    def initialize(self):
        self._service = None

    def options(self, id):
        self.write({"success": True, "id": id})
        self.finish_no_db_session()

    @asynchronous
    @gen.engine
    def get(self, id):
        try:
            http_client = AsyncHTTPClient()
            url = config.ADMIN_API_URL + "{0}/".format(self._service) + id
            headers = {"Content-Type": "application/json; charset=UTF-8"}
            response = yield http_client.fetch(url, method="GET", headers=headers)
            body = response.body.decode("utf-8")
            # jsonResponse = json.loads(body)
            self.write(body)
        except Exception as e:
            response = {
                "success": False,
                "message": "Something went wrong."
            }
            logging.exception(e)
            self.write(response)
        self.finish_no_db_session()

    @asynchronous
    @gen.engine
    def delete(self, id):
        try:
            http_client = AsyncHTTPClient()
            url = config.ADMIN_API_URL + "{0}/".format(self._service) + id
            headers = {"Content-Type": "application/json; charset=UTF-8"}
            response = yield http_client.fetch(url, method="DELETE", headers=headers)
            body = response.body.decode("utf-8")
            json_response = json.loads(body)
            self.write(json_response)
        except Exception as e:
            response = {
                "success": False,
                "message": "Something went wrong."
            }
            logging.exception(e)
            self.write(response)
        self.finish_no_db_session()
