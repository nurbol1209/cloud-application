-- Исходная схема ЛР №14, от которой начинается история Alembic.
-- Выполняется официальным образом PostgreSQL только при инициализации
-- пустого каталога данных (/docker-entrypoint-initdb.d).

CREATE TABLE service_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    description VARCHAR(255)
);

CREATE TABLE services (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    type_id INTEGER REFERENCES service_types(id),
    status VARCHAR(20)
);

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
SELECT 'Monitoring Service', id, 'running'
FROM service_types
WHERE name = 'monitoring';
