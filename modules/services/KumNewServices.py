import datetime
import logging

from tornado.concurrent import run_on_executor

from core.BaseService import BaseService
from core.helpers import FilterHelper, SortParser
from modules.models.models import KumNew, KumNewsTopic,KumTopic
from sqlalchemy.sql.expression import text
from core.definition import BooleanAlias

class KumNewServices(BaseService):
    def __init__(self, db_session):
        super().__init__(db_session)
        self.db_session = db_session

    def row_to_asdict(self, row):
        d = row._asdict()
        d['created_date'] = row.created_date.strftime("%d-%m-%YT%H:%M:%S") if row.created_date is not None else None
        d['updated_date'] = row.updated_date.strftime("%d-%m-%YT%H:%M:%S") if row.updated_date is not None else None
        return d

    def row_to_dict(self, row):
        d = {}
        d['id'] = row.id
        d['newsid'] = row.newsid
        d['title'] = row.title
        d['content'] = row.content
        d['status'] = row.status

        return d

    def rows_to_dict(self, rows):
        data = []
        for row in rows:
            d = self.row_to_dict(row)
            data.append(d)
        return data

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
            news.created_date = datetime.datetime.now().isoformat()
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

    @run_on_executor
    def find(self, filter: str, page=0, perPage=0, orderBy=""):
        print("tes" + filter)
        try:
            print("1")
            fh = FilterHelper()
            fh.parse(filter)
            print(fh.get_params())
            rows = self.db_session.query(KumNew) \
                .join(KumNewsTopic) \
                .filter(KumNew.isdeleted == BooleanAlias.FALSE) \
                .filter(text(fh.get_sql_filter())) \
                .params(fh.get_params())

            if orderBy:
                sortParser = SortParser(orderBy)
                rows = rows.order_by(sortParser.parse())
            if page > 0:
                rows = rows.limit(perPage)
            if perPage > 0:
                rows = rows.offset((page - 1) * perPage)
            return self.rows_to_dict(rows), rows.count()
        except Exception as e:
            logging.exception("Error on find method of SysRolePrivilegeService")
            print(e)
        return None

    @run_on_executor
    def update(self, kumNew):
        result = {"success": True}
        print(kumNew)
        try:

                objdb = self.db_session.query(KumNew) \
                    .filter(KumNew.id == kumNew['id']).one()
                # objdb.id = str(uuid.uuid4())
                print(objdb)
                objdb.newsid = kumNew.get('newsid') if kumNew.get('newsid') else objdb.newsid
                objdb.content = kumNew.get('content') if kumNew.get('content') else objdb.content
                objdb.title = kumNew.get('title') if kumNew.get('title') else objdb.title
                objdb.status = kumNew.get('status') if kumNew.get('status') else objdb.status
                for t in kumNew.get('topics'):
                    topic = KumNewsTopic()

                    topic.newsid = objdb.id
                    topic.topicid = t.get('id') if t.get('id') else None

                    self.db_session.add(topic)
        except Exception as e:
            logging.exception("Error on update method of SysPrivilegeService")
            result["success"] = False
            result["errors"] = {"error": "Something went wrong."}
        return result


    @run_on_executor
    def delete(self, id: str):
        result = {"success": True}
        print(id)
        try:
            print("ntap")
            objdb = self.db_session.query(KumNew) \
                .filter(KumNew.id == id).one()
            print("ntap1")
            objdb.isdeleted = True
            print("ntap")
            objdb.updated_date = datetime.datetime.now()
        except Exception as e:
            logging.exception("Error on delete method of SysUserService")
            result["success"] = False
            result["errors"] = {"error": "Something went wrong."}
        return result
