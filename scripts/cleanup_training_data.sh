#!/bin/bash
# Clean up data/ directory (moxi pipelines)

set -e

cd "$(dirname "$0")/.."
DATA_DIR="data"

echo "Cleaning up data directory..."

mkdir -p "$DATA_DIR/collection" "$DATA_DIR/chunks" "$DATA_DIR/sft" "$DATA_DIR/processed"
ARCHIVE_DIR="$DATA_DIR/archive"
mkdir -p "$ARCHIVE_DIR"

# Archive old / legacy files (do not delete)
for f in training_dataset.json training_dataset_backup.json test_single.json cleaning_report.json validation_report.json visualization.html simple_mvp_dataset.json; do
    for base in "$DATA_DIR/sft" "$DATA_DIR"; do
        if [ -f "$base/$f" ]; then
            echo "Archiving $f..."
            mv "$base/$f" "$ARCHIVE_DIR/"
        fi
    done
done

echo ""
echo "Cleanup complete."
echo "README data: awesome_readme_clean.json (and MongoDB readme_samples)."
echo "Next: make moxi-collect (writes to data/collection/)"
