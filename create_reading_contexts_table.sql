CREATE TABLE IF NOT EXISTS reading_contexts (
    context_id SERIAL PRIMARY KEY,
    context_name VARCHAR(255) UNIQUE NOT NULL
);