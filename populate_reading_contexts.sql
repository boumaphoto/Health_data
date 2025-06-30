INSERT INTO reading_contexts (context_name)
SELECT DISTINCT reading_context FROM blood_glucose_meter
ON CONFLICT (context_name) DO NOTHING;