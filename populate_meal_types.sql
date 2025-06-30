INSERT INTO meal_types (meal_type_name)
SELECT DISTINCT meal_type FROM food_log
ON CONFLICT (meal_type_name) DO NOTHING;