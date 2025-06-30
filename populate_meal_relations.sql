INSERT INTO meal_relations (relation_name)
SELECT DISTINCT meal_relation FROM blood_glucose_meter WHERE meal_relation IS NOT NULL
ON CONFLICT (relation_name) DO NOTHING;