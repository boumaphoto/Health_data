UPDATE blood_glucose_meter
SET context_id = (
    SELECT context_id
    FROM reading_contexts
    WHERE reading_contexts.context_name = blood_glucose_meter.reading_context
);