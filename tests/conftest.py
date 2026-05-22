import os
import pytest
from dotenv import load_dotenv
from psycopg import Connection, connect
from psycopg_pool import ConnectionPool

from utils.data_generator import WMSDataGenerator

load_dotenv()

DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
BASE_DB_NAME = os.getenv('DB_NAME')


@pytest.fixture(scope="session")
def db_pool(request):
    """Пул соединений с динамической изоляцией баз данных для параллельных потоков."""
    xdist_worker = getattr(request.config, "workerinput", {}).get("workerid")

    if xdist_worker:
        target_db_name = f"{BASE_DB_NAME}_{xdist_worker}"
        admin_dsn = f"host={DB_HOST} port={DB_PORT} user={DB_USER} password={DB_PASSWORD} dbname=postgres"
        with connect(admin_dsn, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(f"DROP DATABASE IF EXISTS {target_db_name};")
                cur.execute(f"CREATE DATABASE {target_db_name};")
    else:
        target_db_name = BASE_DB_NAME

    worker_dsn = f"host={DB_HOST} port={DB_PORT} dbname={target_db_name} user={DB_USER} password={DB_PASSWORD}"

    with ConnectionPool(conninfo=worker_dsn, min_size=1, max_size=5, open=False) as pool:
        pool.open()

        base_dir = os.path.dirname(os.path.dirname(__file__))
        schema_path = os.path.join(base_dir, "db", "schema.sql")
        triggers_path = os.path.join(base_dir, "db", "triggers.sql")

        with pool.connection() as conn:
            with conn.cursor() as cur:
                with open(schema_path, "r", encoding="utf-8") as f:
                    cur.execute(f.read())
                with open(triggers_path, "r", encoding="utf-8") as f:
                    cur.execute(f.read())
            conn.commit()

        yield pool

    if xdist_worker:
        with connect(admin_dsn, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(f"DROP DATABASE IF EXISTS {target_db_name};")


@pytest.fixture(scope="function")
def db_conn(db_pool) -> Connection:
    """Выдает изолированное соединение для каждого теста с авто-откатом изменений."""
    with db_pool.connection() as conn:
        yield conn
        conn.rollback()


@pytest.fixture(scope="session")
def data_gen() -> WMSDataGenerator:
    """Предоставляет доступ к генератору фейковых данных."""
    return WMSDataGenerator()
