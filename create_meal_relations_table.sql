CREATE TABLE IF NOT EXISTS meal_relations (
    relation_id SERIAL PRIMARY KEY,
    relation_name VARCHAR(255) UNIQUE NOT NULL
);