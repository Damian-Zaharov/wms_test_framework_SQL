import allure
import pytest
from psycopg.errors import CheckViolation, RaiseException


@allure.epic("WMS Валидация ограничений")
@allure.feature("Лимиты грузоподъемности курьеров")
@allure.story("Груз меньше лимита")
def test_insert_valid_foot_courier(db_conn, data_gen):
    """Проверяем, что валидный пеший курьер успешно создается через Faker"""
    # Генерируем заведомо валидного пешехода (до 15 кг)
    courier_data = data_gen.generate_courier(transport_type="foot")
    courier_data["max_weight_capacity"] = 12.00  # Гарантируем валидность

    with db_conn.cursor() as cur:
        cur.execute("""
                    INSERT INTO couriers (name, transport_type, max_weight_capacity, geo_zone)
                    VALUES (%(name)s, %(transport_type)s, %(max_weight_capacity)s, %(geo_zone)s) RETURNING id;
                    """, courier_data)
        courier_id = cur.fetchone()[0]

    assert courier_id is not None


@allure.epic("WMS Валидация ограничений")
@allure.feature("Лимиты грузоподъемности курьеров")
@allure.story("Груз больше лимита")
def test_invalid_foot_courier_constraint(db_conn, data_gen):
    """Проверяем, что CHECK-constraint не пропустит пешехода тяжелее 15 кг"""
    courier_data = data_gen.generate_courier(transport_type="foot")
    courier_data["max_weight_capacity"] = 20.00  # Нарушаем бизнес-правило базы

    with db_conn.cursor() as cur:
        # Ожидаем, что Postgres выбросит исключение CheckViolation
        with pytest.raises(CheckViolation) as exc_info:
            cur.execute("""
                        INSERT INTO couriers (name, transport_type, max_weight_capacity, geo_zone)
                        VALUES (%(name)s, %(transport_type)s, %(max_weight_capacity)s, %(geo_zone)s);
                        """, courier_data)

    # Проверяем, что ошибка вызвана именно нашим ограничением
    assert "check_foot_courier_weight" in str(exc_info.value)


@allure.epic("WMS Валидация ограничений")
@allure.feature("Лимиты грузоподъемности курьеров")
@allure.story("Запрет назначения тяжелых заказов")
def test_courier_weight_limit_trigger(db_conn, data_gen):
    """Проверяем работу триггера: нельзя назначить тяжелый заказ на пешего курьера"""
    with db_conn.cursor() as cur:
        # 1. Генерируем и сохраняем пешего курьера через Faker (лимит до 15 кг)
        courier_data = data_gen.generate_courier(transport_type="foot")
        courier_data["max_weight_capacity"] = 12.00  # Явно фиксируем небольшой лимит

        cur.execute("""
                    INSERT INTO couriers (name, transport_type, max_weight_capacity, geo_zone)
                    VALUES (%(name)s, %(transport_type)s, %(max_weight_capacity)s, %(geo_zone)s) RETURNING id;
                    """, courier_data)
        courier_id = cur.fetchone()[0]

        # 2. Генерируем тяжелый заказ (50 кг)
        order_data = data_gen.generate_order()
        order_data["weight"] = 50.00
        order_data["courier_id"] = courier_id

        # 3. Ожидаем, что триггер выбросит RaiseException (ошибка бизнес-логики)
        with pytest.raises(RaiseException) as exc_info:
            cur.execute("""
                        INSERT INTO orders (weight, volume, geo_zone, status, courier_id)
                        VALUES (%(weight)s, %(volume)s, %(geo_zone)s, %(status)s, %(courier_id)s);
                        """, order_data)

    # Проверяем, что сработала именно наша кастомная ошибка из триггера
    assert "CourierWeightLimitExceeded" in str(exc_info.value)