CREATE TABLE IF NOT EXISTS meal_types (
    meal_type_id SERIAL PRIMARY KEY,
    meal_type_name VARCHAR(255) UNIQUE NOT NULL
);