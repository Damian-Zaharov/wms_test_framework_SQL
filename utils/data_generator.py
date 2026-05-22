import random
from faker import Faker


class WMSDataGenerator:
    def __init__(self):
        # Инициализируем Faker с русской локализацией для реалистичных имён
        self.fake = Faker("ru_RU")
        # Фиксируем список гео-зон, которые знает наша система
        self.geo_zones = ["zone_center", "zone_north", "zone_south", "zone_east", "zone_west"]

    def generate_courier(self, transport_type: str = None) -> dict:
        """Генерирует валидные данные для курьера в зависимости от транспорта"""
        if not transport_type:
            transport_type = random.choice(["foot", "bike", "car"])

        # Устанавливаем лимиты веса в зависимости от типа транспорта
        if transport_type == "foot":
            # Пешеход: до 15 кг по нашему CHECK-constraint
            max_weight = round(random.uniform(5.0, 15.0), 2)
        elif transport_type == "bike":
            # Велосипедист: от 15 до 30 кг
            max_weight = round(random.uniform(15.1, 30.0), 2)
        else:
            # Автомобиль: от 50 до 500 кг
            max_weight = round(random.uniform(50.0, 500.0), 2)

        return {
            "name": self.fake.name(),
            "transport_type": transport_type,
            "max_weight_capacity": max_weight,
            "geo_zone": random.choice(self.geo_zones),
            "is_active": True
        }

    def generate_order(self, geo_zone: str = None, weight: float = None) -> dict:
        """Генерирует данные для случайного заказа"""
        return {
            "weight": weight if weight is not None else round(random.uniform(0.5, 25.0), 2),
            "volume": round(random.uniform(0.1, 5.0), 2),
            "geo_zone": geo_zone if geo_zone else random.choice(self.geo_zones),
            "status": "created"
        }
