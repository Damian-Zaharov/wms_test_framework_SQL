import pytest
import allure
from psycopg.errors import RaiseException


@allure.epic("WMS Валидация ограничений")
@allure.feature("Контроль ресурсов склада")
@allure.story("Переполнение объема ячейки хранения")
@allure.severity(allure.severity_level.CRITICAL)
def test_cell_volume_overflow_trigger(db_conn, data_gen):
    """Тест проверяет, что база выдает ошибку при переполнении объема ячейки"""
    with db_conn.cursor() as cur:
        # 1. Создаем тестовую ячейку с лимитом объема 10.00 единиц
        cur.execute("""
                    INSERT INTO storage_locations (name, location_type, max_volume_units)
                    VALUES ('Тестовая ячейка A-101', 'cell', 10.00) RETURNING id;
                    """)
        cell_id = cur.fetchone()[0]

        # 2. Генерируем заказ, который идеально помещается (объем 9.00)
        order_fit = data_gen.generate_order()
        order_fit["volume"] = 9.00
        order_fit["cell_id"] = cell_id

        cur.execute("""
                    INSERT INTO orders (weight, volume, geo_zone, status, cell_id)
                    VALUES (%(weight)s, %(volume)s, %(geo_zone)s, %(status)s, %(cell_id)s);
                    """, order_fit)

        # 3. Пытаемся впихнуть второй заказ (объем 2.00). В сумме будет 11.00 > 10.00
        order_overflow = data_gen.generate_order()
        order_overflow["volume"] = 2.00
        order_overflow["cell_id"] = cell_id

        # 4. Проверяем, что база выкидывает корректную ошибку переполнения
        with pytest.raises(RaiseException) as exc_info:
            cur.execute("""
                        INSERT INTO orders (weight, volume, geo_zone, status, cell_id)
                        VALUES (%(weight)s, %(volume)s, %(geo_zone)s, %(status)s, %(cell_id)s);
                        """, order_overflow)

    # Проверяем имя нашего кастомного исключения из триггера
    assert "CellVolumeOverflow" in str(exc_info.value)
