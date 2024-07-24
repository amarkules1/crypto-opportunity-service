import os
import sqlalchemy


def get_connection():
    return sqlalchemy.create_engine(os.getenv("DATABASE_CONN_STRING")).connect()
