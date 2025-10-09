-- AutoDoc Database Initialization Script
-- Creates multiple databases for different environments

-- Create databases for different environments
CREATE DATABASE autodoc_dev;
CREATE DATABASE autodoc_test;
CREATE DATABASE autodoc_prod;

-- Grant permissions to autodoc user
GRANT ALL PRIVILEGES ON DATABASE autodoc TO autodoc;
GRANT ALL PRIVILEGES ON DATABASE autodoc_dev TO autodoc;
GRANT ALL PRIVILEGES ON DATABASE autodoc_test TO autodoc;
GRANT ALL PRIVILEGES ON DATABASE autodoc_prod TO autodoc;

-- Create extensions that might be needed
\c autodoc_dev;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

\c autodoc_test;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

\c autodoc_prod;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

\c autodoc;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
