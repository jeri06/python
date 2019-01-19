import logging

from tornado.concurrent import run_on_executor

from core.BaseService import BaseService
from modules.models.models import KumNew, KumNewsTopic


class KumNewServices(BaseService):
    def __init__(self, db_session):
        super().__init__(db_session)
        self.db_session = db_session

    @run_on_executor
    def create(self, kumNews):
        result = {"success": True}
        try:
            news = KumNew()

            # objdb.id = int(time.time())
            news.newsid = kumNews.get('newsid') if kumNews.get('newsid') else None
            news.content = kumNews.get('content') if kumNews.get('content') else None
            news.title = kumNews.get('title') if kumNews.get('title') else None
            news.status = kumNews.get('status') if kumNews.get('status') else None
            self.db_session.add(news)
            self.db_session.flush()
            for t in kumNews.get('topics'):
                topic = KumNewsTopic()

                topic.newsid = news.id
                topic.topicid = t.get('id') if t.get('id') else None

                self.db_session.add(topic)

        except Exception as e:
            logging.exception("Error on create method of SysRolePrivilegeService")
            result["success"] = False
            result["errors"] = {"error": "Something went wrong."}
            print(e)
        return result
