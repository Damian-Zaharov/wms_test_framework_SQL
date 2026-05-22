-- Обход иерархии склада снизу вверх (от конкретной ячейки до головного склада)
-- Используется для сборки полного пути локации при комплектации заказа
WITH RECURSIVE location_path AS (
    -- Базовая часть (Anchor): стартуем с нашей целевой ячейки
    SELECT id, parent_id, name, location_type, 1 as level
    FROM storage_locations
    WHERE id = %(cell_id)s

    UNION ALL

    -- Рекурсивная часть: присоединяем родительские локации
    SELECT child.id, child.parent_id, child.name, child.location_type, path.level + 1
    FROM storage_locations child
    JOIN location_path path ON child.id = path.parent_id
)
SELECT name, location_type
FROM location_path
ORDER BY level DESC; -- Сортируем от верхнего уровня (склад) к нижнему (ячейка)
