CREATE TABLE IF NOT EXISTS food_items (
    food_item_id SERIAL PRIMARY KEY,
    food_item_name VARCHAR(255) UNIQUE NOT NULL,
    brand VARCHAR(255),
    serving_size VARCHAR(255)
);