-- Начальные данные Cloud Application

INSERT INTO service_types (name, description)
VALUES
    ('application', 'Application service'),
    ('database', 'Database service'),
    ('monitoring', 'Monitoring service');

INSERT INTO services (name, type_id, status)
SELECT 'Web Service', id, 'running'
FROM service_types
WHERE name = 'application';

INSERT INTO services (name, type_id, status)
SELECT 'Database Service', id, 'running'
FROM service_types
WHERE name = 'database';

INSERT INTO services (name, type_id, status)
SELECT 'Monitoring Service', id, 'maintenance'
FROM service_types
WHERE name = 'monitoring';
