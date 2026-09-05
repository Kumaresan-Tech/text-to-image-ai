-- ============================================
-- PostgreSQL Initialization Script
-- ============================================
-- Runs on first container startup via docker-entrypoint-initdb.d

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create application user with limited privileges
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'text2img_app') THEN
        CREATE ROLE text2img_app LOGIN PASSWORD 'CHANGE_ME';
    END IF;
END
$$;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE text2img TO text2img_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO text2img_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO text2img_app;
