import os
import sqlalchemy


def get_connection():
    return sqlalchemy.create_engine(os.getenv("SUPABASE_CONN_STRING")).connect()
