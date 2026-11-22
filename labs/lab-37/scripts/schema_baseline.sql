-- Исходная схема Cloud Application для локального SQLite-режима.
-- Соответствует состоянию после ЛР № 14 (до миграций Alembic).

CREATE TABLE service_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50),
    description VARCHAR(255)
);

CREATE TABLE services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100),
    type_id INTEGER REFERENCES service_types(id),
    status VARCHAR(20)
);

INSERT INTO service_types (id, name, description)
VALUES
    (1, 'application', 'Application service'),
    (2, 'database', 'Database service'),
    (3, 'monitoring', 'Monitoring service');

INSERT INTO services (name, type_id, status)
VALUES
    ('Web Service', 1, 'running'),
    ('Database Service', 2, 'running'),
    ('Monitoring Service', 3, 'maintenance');
