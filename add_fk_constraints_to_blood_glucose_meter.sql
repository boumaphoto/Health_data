ALTER TABLE blood_glucose_meter
ADD CONSTRAINT fk_reading_context
FOREIGN KEY (context_id)
REFERENCES reading_contexts (context_id),
ADD CONSTRAINT fk_meal_relation
FOREIGN KEY (relation_id)
REFERENCES meal_relations (relation_id);