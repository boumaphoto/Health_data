UPDATE food_log
SET
    meal_type_id = mt.meal_type_id,
    food_item_id = fi.food_item_id
FROM
    meal_types mt,
    food_items fi
WHERE
    food_log.meal_type = mt.meal_type_name AND
    food_log.food_item = fi.food_item_name;