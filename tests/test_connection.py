import allure

@allure.epic("Инфраструктура")
@allure.feature("База данных PostgreSQL")
@allure.story("Проверка сетевого соединения с СУБД")
@allure.severity(allure.severity_level.BLOCKER)
def test_postgres_version(db_conn):
    """Тест проверяет, что мы можем успешно выполнить запрос к PostgreSQL"""
    with db_conn.cursor() as cur:
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]

    assert "PostgreSQL" in version
    print(f"\n[Успех] Подключено к: {version}")
