#!/bin/bash
# 清理不需要的文件

echo "🧹 开始清理..."

# 删除旧项目相关文件
rm -f file_browser_ui.html
rm -f file_browser_data.json
rm -f repo_issue_viewer.html
rm -f repo_readme_viewer.html
rm -f generate_moxi_architecture.py
rm -f generate_detailed_architecture.py
rm -f generate_repo_with_deepwiki_style.py
rm -f find_architecture_readmes.py
rm -f find_best_architecture_readmes.py
rm -f find_real_architecture_readmes.py
rm -f check_manual_repos.py
rm -f check_specific_repos.py
rm -f search_architecture_repos.py

# 删除旧数据文件
rm -f training_data/awesome_readme_test.json
rm -f training_data/test_clean_readme.json
rm -f training_data/test_markdown.json
rm -f training_data/training_dataset.json
rm -f training_data/training_dataset_backup.json
rm -f training_data/simple_mvp_dataset.json
rm -f architecture_readmes_examples.json
rm -f best_architecture_readmes.json
rm -f manual_readme_check.json
rm -f readme_check_results.json
rm -f real_architecture_readmes.json

# 删除旧 HTML 文件
rm -f moxi_architecture_visualization.html
rm -f moxi_detailed_architecture.html
rm -f feature_request_workflow.html
rm -f fun_project_ideas_visualization.html
rm -rf deepwiki_output/

# 删除旧文档（已整合）
rm -f IMPROVED_INPUT_APPROACH.md
rm -f REVISED_INPUT_APPROACH.md
rm -f FUN_PROJECT_IDEAS.md

echo "✅ 清理完成！"
