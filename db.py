'''
Created on Apr 1, 2016

@author: kakan
'''

from config import databases
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import exc
from sqlalchemy import event
from sqlalchemy.pool import Pool
from sqlalchemy.orm.scoping import scoped_session


class EngineFactory:

    def create_engine(self):
        engines = {}
        for key in databases:
            strcon = '{0}://{1}:{2}@{3}:{4}/{5}'.format(
                databases.get(key).get("driver"),
                databases.get(key).get("user"),
                databases.get(key).get("password"),
                databases.get(key).get("host"),
                databases.get(key).get("port"),
                databases.get(key).get("dbname")
            )
            engine = create_engine(strcon, pool_size=10, max_overflow=-1, pool_recycle=(5),
                                   isolation_level="READ UNCOMMITTED")
            engines[key] = engine
        return engines


engineFactory = EngineFactory()
engines = engineFactory.create_engine()


@event.listens_for(Pool, "checkout")
def ping_connection(dbapi_connection, connection_record, connection_proxy):
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("SELECT 1")
    except:
        # raise DisconnectionError - pool will try
        # connecting again up to three times before raising.
        for engine in engines:
            engines[engine].connect()
        # raise exc.DisconnectionError()
    cursor.close()


class SessionFactory():
    __instance = None

    def __init__(self):
        self.__engine = None
        self.__connection = None
        self.__session = None

    @staticmethod
    def instance(requiresNew=False, engineName="default"):
        engine = engines.get(engineName)
        sessionFac = None
        if not requiresNew:
            if SessionFactory.__instance == None:
                SessionFactory.__instance = SessionFactory()
                SessionFactory.__instance.create_session(engine)
            sessionFac = SessionFactory.__instance
        else:
            sessionFac = SessionFactory()
            sessionFac.create_session(engine)
        return sessionFac

    def create_session(self, engine):
        self.__engine = engine
        self.__connection = engine.connect()
        Session = sessionmaker(bind=self.__engine)
        self.__session = Session()

    def get_session(self):
        return self.__session

    def get_engine(self):
        return self.__engine

    def get_connection(self):
        return self.__connection


if __name__ == '__main__':
    sessFac = SessionFactory().instance(True)
    sess2Fac = SessionFactory().instance(True)






