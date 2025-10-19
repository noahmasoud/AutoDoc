#!/bin/bash
# Development environment variables for AutoDoc
# Source this file before running alembic or other commands:
#   source scripts/dev-env.sh

export SECRET_KEY="dev-secret-key-change-in-production-must-be-32-chars-minimum"
export JWT_SECRET_KEY="dev-jwt-secret-key-must-be-32-chars-minimum"

echo "✅ Development environment variables set!"
echo "   SECRET_KEY: ${SECRET_KEY:0:20}..."
echo "   JWT_SECRET_KEY: ${JWT_SECRET_KEY:0:20}..."

