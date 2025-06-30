ALTER TABLE food_log
ADD CONSTRAINT fk_meal_type
FOREIGN KEY (meal_type_id)
REFERENCES meal_types (meal_type_id),
ADD CONSTRAINT fk_food_item
FOREIGN KEY (food_item_id)
REFERENCES food_items (food_item_id);