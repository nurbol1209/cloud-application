-- Основные SQL-операции Cloud Application

-- 1. Получение всех сервисов
SELECT *
FROM services;

-- 2. Получение сервисов в состоянии running
SELECT *
FROM services
WHERE status = 'running';

-- 3. Сортировка по названию
SELECT id, name, status
FROM services
ORDER BY name;

-- 4. Объединение таблиц
SELECT
    services.id,
    services.name,
    service_types.name AS type,
    services.status
FROM services
JOIN service_types
    ON service_types.id = services.type_id
ORDER BY services.id;

-- 5. Добавление сервиса
INSERT INTO services (name, type_id, status)
SELECT 'Backup Service', id, 'running'
FROM service_types
WHERE name = 'application';

-- 6. Изменение состояния
UPDATE services
SET status = 'maintenance'
WHERE name = 'Backup Service';

-- 7. Удаление сервиса
DELETE FROM services
WHERE name = 'Backup Service';

-- 8. Проверка внешнего ключа: тип 999 не существует
-- INSERT INTO services (name, type_id, status)
-- VALUES ('Unknown Type Service', 999, 'running');
-- Ожидается ошибка foreign key violation.

-- 9. Сервисы с типом, в названии которого есть 'data'
SELECT
    services.name,
    service_types.name AS type
FROM services
JOIN service_types
    ON service_types.id = services.type_id
WHERE service_types.name LIKE '%data%';

-- 10. Количество сервисов по состояниям
SELECT status, COUNT(*) AS services_count
FROM services
GROUP BY status
ORDER BY status;

-- Самостоятельное задание: полный жизненный цикл Backup Service
-- INSERT → SELECT → UPDATE → SELECT → DELETE → SELECT
