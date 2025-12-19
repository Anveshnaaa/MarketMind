#!/bin/bash
# Run the complete data pipeline

set -e

echo "=========================================="
echo "Startup Market Analyzer - Data Pipeline"
echo "=========================================="
echo ""

echo "Step 1: Data Ingestion (Raw Layer)"
echo "-----------------------------------"
uv run python -m src.pipeline.ingest

echo ""
echo "Step 2: Data Cleaning (Clean Layer)"
echo "-----------------------------------"
uv run python -m src.pipeline.clean

echo ""
echo "Step 3: Data Aggregation (Aggregated Layer)"
echo "--------------------------------------------"
uv run python -m src.pipeline.aggregate

echo ""
echo "=========================================="
echo "Pipeline completed successfully!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Run the dashboard: uv run streamlit run dashboard/app.py"
echo "2. Check MongoDB collections for data"


