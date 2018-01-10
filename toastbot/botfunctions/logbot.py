"""
Database support for the bot logging functionality.
"""

import sqlite3
import sqlalchemy
import sqlalchemy.ext.declarative as declarative
import sqlalchemy.orm as orm
import sqlalchemy.util as util

import logging


Base = declarative.declarative_base()


class DBSessions:
    DATABASE_SESSION_MAKER = None


class LogSessionConfigs:
    """
    Class to hold characters currently active, and lists of logging sessions that they're attached to.
    """
    active_logs = dict()

    @staticmethod
    def add_user(character_name):
        LogSessionConfigs.active_logs[character_name] = list()
        logging.info('{} added to current users.'.format(character_name))

    @staticmethod
    def add_log_to_user(character_name, log_id):
        LogSessionConfigs.active_logs[character_name].append(log_id)
        logging.info('{} added to log {}.'.format(character_name, log_id))


class Character(Base):
    __tablename__='character'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String)
    username = sqlalchemy.Column(sqlalchemy.String)


class Text(Base):
    __tablename__='text'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    timestamp = sqlalchemy.Column(sqlalchemy.DateTime)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('character.id'))
    log_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('log.id'))
    text = sqlalchemy.Column(sqlalchemy.String)


class Log(Base):
    __tablename__='log'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String)
    timestamp = sqlalchemy.Column(sqlalchemy.DateTime)


class TextResponse:
    def __init__(self, name, timestamp, text):
        self.name = name
        self.timestamp = timestamp
        self.text = text

    def __str__(self):
        result = '{name}: {timestamp}\n{text}\n'.format(name=self.name, timestamp=self.timestamp, text=self.text)
        return result


def initialize_engine():
    """
    Initialize sqlalchemy engine for database access.
    :return: sqalchemy SQLite engine.
    """
    engine = sqlalchemy.create_engine('sqlite+pysqlite:///data/logdata.db', module=sqlite3)
    inspector = sqlalchemy.inspect(engine)
    if 'text' not in inspector.get_table_names():
        initialize_database(engine)
    return engine


def initialize_database(engine):
    """
    If necessary, create needed tables for the database. Run this against the engine
    if database does not yet exist.

    :param engine: SQLAlchemy engine.
    :return: The same engine passed into the function.
    """

    Base.metadata.create_all(engine)
    return engine


def create_session(engine):
    if not DBSessions.DATABASE_SESSION_MAKER:
        DBSessions.DATABASE_SESSION_MAKER = orm.sessionmaker(bind=engine)
    session = DBSessions.DATABASE_SESSION_MAKER()
    return session


def add_log(session, name, timestamp):
    new_log = Log(name=name, timestamp=timestamp)
    session.add(new_log)
    session.commit()
    return session


def get_log_id(session, name, timestamp=None):
    logging.info("Requested log {}".format(name))
    try:
        if timestamp is not None:
            log_id = session.query(Log).filter_by(name=name, timestamp=timestamp).one().id
        else:
            log_id = session.query(Log).filter_by(name=name).one().id
    except orm.exc.NoResultFound:
        log_id = None
    logging.info('Found log {}'.format(log_id))
    return log_id


def add_new_text(session, timestamp, character_name, username, text, log_id):
    try:
        user_id = session.query(Character).filter_by(name=character_name).one().id
    except orm.exc.NoResultFound:
        add_new_character(session, character_name, username)
        user_id = session.query(Character).filter_by(name=character_name).one().id
    new_text = Text(timestamp=timestamp, user_id=user_id, text=text, log_id=log_id)
    session.add(new_text)
    session.commit()
    logging.info('Text added for log ID {}, character {}'.format(log_id, character_name))
    return session


def add_new_character(session, character_name, username):
    new_character = Character(name=character_name, username=username)
    session.add(new_character)
    session.commit()
    logging.info('Name added: {} for {}'.format(character_name, username))
    return session


def get_text(session, log_id):
    raw_results = session.query(Text, Character).filter(Text.log_id == log_id).order_by(Text.timestamp).all()
    processed_results = [TextResponse(name=result.Character.name,
                                      text=result.Text.text,
                                      timestamp=result.Text.timestamp
                                      )
                         for result in raw_results
                         ]
    logging.info('{} lines found'.format(len(processed_results)))
    return processed_results
