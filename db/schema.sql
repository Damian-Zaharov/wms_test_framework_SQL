-- 1. Иерархия склада: Склад -> Зона -> Стеллаж -> Ячейка
CREATE TABLE storage_locations (
    id SERIAL PRIMARY KEY,
    parent_id INTEGER REFERENCES storage_locations(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    location_type VARCHAR(20) NOT NULL CHECK (location_type IN ('warehouse', 'zone', 'rack', 'cell')),
    max_volume_units NUMERIC(10, 2), -- Максимальный объем (заполняется только для ячеек 'cell')
    current_volume_units NUMERIC(10, 2) DEFAULT 0.00 CHECK (current_volume_units >= 0)
);

-- Ограничение на уровне таблицы: объем может быть только у ячеек
ALTER TABLE storage_locations ADD CONSTRAINT check_cell_volume
CHECK (
    (location_type = 'cell' AND max_volume_units IS NOT NULL AND max_volume_units > 0) OR
    (location_type != 'cell' AND max_volume_units IS NULL)
);

-- 2. Курьеры, их транспорт, лимиты и гео-зоны
CREATE TABLE couriers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    transport_type VARCHAR(20) NOT NULL CHECK (transport_type IN ('foot', 'bike', 'car')),
    max_weight_capacity NUMERIC(10, 2) NOT NULL, -- Максимальный вес в кг
    geo_zone VARCHAR(50) NOT NULL,               -- Упрощенная гео-зона (например, 'zone_center', 'zone_north')
    is_active BOOLEAN DEFAULT TRUE
);

-- Ограничение для пешеходов: физически не можем дать пешему курьеру лимит больше 15 кг
ALTER TABLE couriers ADD CONSTRAINT check_foot_courier_weight
CHECK (
    (transport_type = 'foot' AND max_weight_capacity <= 15.00) OR
    (transport_type != 'foot')
);

-- 3. Заказы
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    weight NUMERIC(10, 2) NOT NULL CHECK (weight > 0),
    volume NUMERIC(10, 2) NOT NULL CHECK (volume > 0),
    geo_zone VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'created'
        CHECK (status IN ('created', 'stored', 'assigned', 'delivering', 'delivered', 'cancelled')),
    cell_id INTEGER REFERENCES storage_locations(id), -- Где лежит на складе
    courier_id INTEGER REFERENCES couriers(id)        -- Кто везет
);
