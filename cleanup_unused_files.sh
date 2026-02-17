#!/bin/bash
# Clean up unused test files, temporary files, and outdated documentation

cd "$(dirname "$0")"

echo "🧹 Cleaning up unused files..."
echo ""

# Test/temporary Python scripts
echo "📝 Removing test/temporary Python scripts..."
rm -f test_architecture_generation.py
rm -f test_file_browser.py
rm -f evaluate_diagram_quality.py
rm -f generate_reference_diagram.py
rm -f generate_folder_descriptions.py

# Test/temporary HTML files
echo "🌐 Removing test/temporary HTML files..."
rm -f test_data_load.html
rm -f file_browser_ui_fixed.html  # Keep only file_browser_ui.html

# Outdated documentation files
echo "📚 Removing outdated documentation files..."
rm -f FLOW_EXPLANATION.md  # Replaced by PROJECT_UNDERSTANDING_FOR_BEGINNERS.md
rm -f HOW_TO_VIEW_DESCRIPTIONS.md  # Outdated, info now in file_browser_ui.html
rm -f README_BY_MOXI.md  # Auto-generated, not needed if we have README.md

# Old cleanup script (we'll replace it with this one)
echo "🔧 Removing old cleanup script..."
rm -f cleanup_files.sh

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "📋 Kept important files:"
echo "  ✅ README.md - Main project documentation"
echo "  ✅ PROJECT_UNDERSTANDING_FOR_BEGINNERS.md - Beginner guide"
echo "  ✅ FILE_BY_FILE_EXPLANATION.md - File-by-file explanation"
echo "  ✅ HOW_TO_TRACK_CHANGES.md - Git guide"
echo "  ✅ file_browser_ui.html - Main file browser UI"
echo "  ✅ file_browser_data.json - File browser data (if exists)"
echo "  ✅ start_file_browser.sh - File browser launcher"
echo "  ✅ docs/ directory - All documentation"
echo ""
echo "💡 Note: file_browser_data.json is kept. If it's test data, you can delete it manually."
