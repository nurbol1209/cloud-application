-- Схема базы данных Cloud Application (PostgreSQL)

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

-- Проверка структуры
-- SELECT column_name, data_type
-- FROM information_schema.columns
-- WHERE table_name = 'services'
-- ORDER BY ordinal_position;
