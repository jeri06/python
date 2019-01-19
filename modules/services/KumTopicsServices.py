import logging

from tornado.concurrent import run_on_executor

from core.BaseService import BaseService
from modules.models.models import KumNew, KumNewsTopic,KumTopic


class KumTopicsServices(BaseService):
    def __init__(self, db_session):
        super().__init__(db_session)
        self.db_session = db_session

    @run_on_executor
    def create(self, kumTopic):
        result = {"success": True}
        try:
            topic = KumTopic()

            # objdb.id = int(time.time())
            topic.topicid = kumTopic.get('topicid') if kumTopic.get('topicid') else None


            self.db_session.add(topic)

        except Exception as e:
            logging.exception("Error on create method of SysRolePrivilegeService")
            result["success"] = False
            result["errors"] = {"error": "Something went wrong."}
            print(e)
        return result