INSERT INTO food_items (food_item_name, brand, serving_size)
SELECT DISTINCT food_item, brand, serving_size FROM food_log
ON CONFLICT (food_item_name) DO NOTHING;