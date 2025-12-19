#!/bin/bash
# Run Python scripts inside a Docker container that can resolve internal MongoDB hostnames

# This script is needed because when running from the host machine,
# Python cannot resolve internal Docker hostnames (shard1-a, shard2-a, etc.)

set -e

SCRIPT=$1

if [ -z "$SCRIPT" ]; then
    echo "Usage: ./scripts/run_in_docker.sh <python_script>"
    echo "Example: ./scripts/run_in_docker.sh src.pipeline.ingest"
    exit 1
fi

echo "Running $SCRIPT inside Docker container..."

# Run Python script in a temporary container connected to the MongoDB network
docker run --rm \
    --network bigdataa_mongodb-network \
    -v "$(pwd):/app" \
    -w /app \
    -e MONGODB_HOST=mongos \
    -e MONGODB_PORT=27017 \
    python:3.10-slim \
    bash -c "
        pip install -q uv && \
        uv sync && \
        uv run python -m $SCRIPT
    "

echo "✓ Complete!"
