import os
import pytest
import allure


@allure.epic("WMS Core")
@allure.feature("Топология склада")
@allure.story("Сборка полного пути")
@allure.severity(allure.severity_level.NORMAL)
def test_warehouse_hierarchy_recursive(db_conn):
    """Тест проверяет сборку полного пути локации ячейки с помощью WITH RECURSIVE из внешнего SQL файла"""

    with allure.step("Создание топологии склада (Склад -> Зона -> Стеллаж -> Ячейка)"):
        with db_conn.cursor() as cur:
            cur.execute("""
                        INSERT INTO storage_locations (name, location_type)
                        VALUES ('Центральный Склад', 'warehouse') RETURNING id;
                        """)
            wh_id = cur.fetchone()[0]

            cur.execute("""
                        INSERT INTO storage_locations (name, location_type, parent_id)
                        VALUES ('Зона А (Охлаждаемая)', 'zone', %s) RETURNING id;
                        """, (wh_id,))
            zone_id = cur.fetchone()[0]

            cur.execute("""
                        INSERT INTO storage_locations (name, location_type, parent_id)
                        VALUES ('Стеллаж №5', 'rack', %s) RETURNING id;
                        """, (zone_id,))
            rack_id = cur.fetchone()[0]

            cur.execute("""
                        INSERT INTO storage_locations (name, location_type, parent_id, max_volume_units)
                        VALUES ('Ячейка Б-12', 'cell', %s, 50.00) RETURNING id;
                        """, (rack_id,))
            cell_id = cur.fetchone()[0]

    with allure.step("Чтение рекурсивного запроса из файла db/queries.sql"):
        base_dir = os.path.dirname(os.path.dirname(__file__))
        query_path = os.path.join(base_dir, "db", "queries.sql")

        with open(query_path, "r", encoding="utf-8") as f:
            query = f.read()

        # Прикрепляем текст запроса в Allure для наглядности на ревью
        allure.attach(query, name="Loaded RECURSIVE Query", attachment_type=allure.attachment_type.TEXT)

    with allure.step("Выполнение рекурсивного запроса в БД"):
        with db_conn.cursor() as cur:
            # Передаем словарь, где ключ совпадает с именем в %(cell_id)s
            cur.execute(query, {"cell_id": cell_id})
            full_path = cur.fetchall()

    with allure.step("Валидация корректности собранного пути"):
        # Ожидаем ровно 4 уровня вложенности
        assert len(full_path) == 4

        # Проверяем правильность порядка обхода дерева (сверху вниз)
        assert full_path[0] == ('Центральный Склад', 'warehouse')
        assert full_path[1] == ('Зона А (Охлаждаемая)', 'zone')
        assert full_path[2] == ('Стеллаж №5', 'rack')
        assert full_path[3] == ('Ячейка Б-12', 'cell')
