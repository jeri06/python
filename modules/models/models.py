# coding: utf-8
from sqlalchemy import CHAR, Column, ForeignKey, Integer, SmallInteger, String, text
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class KumNew(Base):
    __tablename__ = 'kum_news'

    newsid = Column(String(255), nullable=False)
    title = Column(String(255))
    content = Column(String(255))
    created_date = Column(TIMESTAMP(precision=0))
    created_by = Column(String(255))
    status = Column(String(255))
    isdeleted = Column(CHAR(255))
    id = Column(Integer, primary_key=True, server_default=text("nextval('kum_news_id_seq'::regclass)"))


class KumTopic(Base):
    __tablename__ = 'kum_topics'

    id = Column(SmallInteger, primary_key=True, server_default=text("nextval('kum_topics_id_seq'::regclass)"))
    topicid = Column(String(255))


class KumNewsTopic(Base):
    __tablename__ = 'kum_news_topics'

    newsid = Column(ForeignKey('kum_news.id'), nullable=False)
    topicid = Column(ForeignKey('kum_topics.id'), nullable=False)
    id = Column(Integer, primary_key=True, server_default=text("nextval('kum_news_topics_id_seq'::regclass)"))

    kum_new = relationship('KumNew')
    kum_topic = relationship('KumTopic')
