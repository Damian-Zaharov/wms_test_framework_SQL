import allure

@allure.epic("Инфраструктура")
@allure.feature("Схема данных (DDL)")
@allure.story("Инициализация структуры таблиц")
@allure.severity(allure.severity_level.BLOCKER)
def test_tables_created(db_conn):
    """Проверяем, что таблицы успешно создались в базе данных"""
    with db_conn.cursor() as cur:
        # Проверяем наличие таблицы orders
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'orders'
            );
        """)
        exists = cur.fetchone()[0]
    assert exists is True
