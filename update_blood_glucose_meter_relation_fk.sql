UPDATE blood_glucose_meter
SET relation_id = (
    SELECT relation_id
    FROM meal_relations
    WHERE meal_relations.relation_name = blood_glucose_meter.meal_relation
);