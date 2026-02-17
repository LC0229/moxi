#!/usr/bin/env python3
"""
智能合并方案 - 完整工作示例
演示如何实现细粒度控制 + 用户选择
"""

import re
from typing import Dict, List, Optional


def parse_moxi_blocks(content: str) -> List[Dict]:
    """
    解析文件中的所有 MOXI 标记块
    
    返回格式：
    [
        {
            'name': 'description',
            'mode': 'AUTO',  # 或 'MANUAL'
            'version': '1',
            'content': '块的内容',
            'full_match': '完整的匹配文本',
            'start_pos': 开始位置,
            'end_pos': 结束位置
        },
        ...
    ]
    """
    # 匹配模式：<!-- MOXI_AUTO:name v1 --> ... <!-- MOXI_AUTO_END:name -->
    pattern = r'<!--\s*MOXI_(AUTO|MANUAL):(\w+)\s+v(\d+)\s*-->(.*?)<!--\s*MOXI_(AUTO|MANUAL)_END:\2\s*-->'
    
    blocks = []
    for match in re.finditer(pattern, content, re.DOTALL):
        mode = match.group(1)  # AUTO 或 MANUAL
        block_name = match.group(2)  # description, installation, etc.
        version = match.group(3)  # 1, 2, 3, etc.
        block_content = match.group(4).strip()
        end_mode = match.group(5)  # 应该和开始模式一致
        
        blocks.append({
            'name': block_name,
            'mode': mode,
            'version': version,
            'content': block_content,
            'full_match': match.group(0),
            'start_pos': match.start(),
            'end_pos': match.end(),
        })
    
    return blocks


def merge_content(
    existing_content: str,
    new_blocks: Dict[str, str],
    auto_detect_changes: bool = True
) -> str:
    """
    合并现有内容和新的自动生成内容
    
    Args:
        existing_content: 现有文件内容
        new_blocks: 新生成的块内容 {block_name: content}
        auto_detect_changes: 是否自动检测用户修改并转为 MANUAL
    
    Returns:
        合并后的内容
    """
    blocks = parse_moxi_blocks(existing_content)
    
    if not blocks:
        # 如果没有现有块，直接生成新内容
        result = existing_content.rstrip() + "\n\n"
        for name, content in new_blocks.items():
            result += f"<!-- MOXI_AUTO:{name} v1 -->\n{content}\n<!-- MOXI_AUTO_END:{name} -->\n\n"
        return result
    
    result_parts = []
    last_pos = 0
    
    for block in blocks:
        # 添加块之前的内容
        result_parts.append(existing_content[last_pos:block['start_pos']])
        
        block_name = block['name']
        mode = block['mode']
        current_version = int(block['version'])
        
        if mode == 'AUTO':
            # AUTO 模式：使用新生成的内容
            if block_name in new_blocks:
                new_content = new_blocks[block_name]
                
                # 自动检测：如果用户修改了内容，转为 MANUAL
                if auto_detect_changes and new_content.strip() != block['content'].strip():
                    # 内容不同，可能是用户修改过，转为 MANUAL
                    print(f"  ⚠️  检测到用户修改了 '{block_name}' 部分，自动转为 MANUAL 模式")
                    result_parts.append(
                        f"<!-- MOXI_MANUAL:{block_name} v{current_version} -->\n"
                        f"{block['content']}\n"
                        f"<!-- MOXI_MANUAL_END:{block_name} -->"
                    )
                else:
                    # 正常更新
                    new_version = current_version + 1
                    result_parts.append(
                        f"<!-- MOXI_AUTO:{block_name} v{new_version} -->\n"
                        f"{new_content}\n"
                        f"<!-- MOXI_AUTO_END:{block_name} -->"
                    )
            else:
                # 没有新内容，保留旧的
                result_parts.append(block['full_match'])
        else:
            # MANUAL 模式：保留用户内容
            print(f"  ✅ 保留用户手动编辑的 '{block_name}' 部分（MANUAL 模式）")
            result_parts.append(block['full_match'])
        
        last_pos = block['end_pos']
    
    # 添加最后的内容
    result_parts.append(existing_content[last_pos:])
    
    # 添加新的块（如果存在）
    existing_block_names = {b['name'] for b in blocks}
    for name, content in new_blocks.items():
        if name not in existing_block_names:
            result_parts.append(
                f"\n<!-- MOXI_AUTO:{name} v1 -->\n{content}\n<!-- MOXI_AUTO_END:{name} -->"
            )
    
    return ''.join(result_parts)


def demo():
    """演示完整工作流程"""
    
    print("=" * 70)
    print("智能合并方案 - 完整工作示例")
    print("=" * 70)
    
    # ============================================================
    # 阶段 1: 首次生成
    # ============================================================
    print("\n【阶段 1】首次生成（所有部分都是 AUTO）")
    print("-" * 70)
    
    initial_content = """# MyProject

<!-- MOXI_AUTO:description v1 -->
## Description
This is a Python library for data processing.
<!-- MOXI_AUTO_END:description -->

<!-- MOXI_AUTO:installation v1 -->
## Installation
```bash
pip install myproject
```
<!-- MOXI_AUTO_END:installation -->

<!-- MOXI_AUTO:usage v1 -->
## Usage
```python
from myproject import process_data
result = process_data(data)
```
<!-- MOXI_AUTO_END:usage -->
"""
    
    print("初始文件内容：")
    print(initial_content)
    
    # ============================================================
    # 阶段 2: 用户修改了 Usage 部分
    # ============================================================
    print("\n【阶段 2】用户修改了 Usage 部分（改为 MANUAL）")
    print("-" * 70)
    
    user_modified_content = """# MyProject

<!-- MOXI_AUTO:description v1 -->
## Description
This is a Python library for data processing.
<!-- MOXI_AUTO_END:description -->

<!-- MOXI_AUTO:installation v1 -->
## Installation
```bash
pip install myproject
```
<!-- MOXI_AUTO_END:installation -->

<!-- MOXI_MANUAL:usage v1 -->
## Usage
```python
from myproject import process_data

# Example 1: Basic usage
result = process_data(data)

# Example 2: Advanced usage with options
result = process_data(data, options={"format": "json"})
```
<!-- MOXI_MANUAL_END:usage -->
"""
    
    print("用户修改后的文件：")
    print(user_modified_content)
    
    # ============================================================
    # 阶段 3: 代码更新后，自动重新生成
    # ============================================================
    print("\n【阶段 3】代码更新后，自动重新生成")
    print("-" * 70)
    
    # 模拟新生成的内容
    new_blocks = {
        'description': '## Description\nThis is a Python library for advanced data processing with ML support.',
        'installation': '## Installation\n```bash\npip install myproject[ml]\n```',
        'usage': '## Usage\n```python\nfrom myproject import process_data\nresult = process_data(data, options={"format": "json"})\n```',
    }
    
    print("新生成的内容：")
    for name, content in new_blocks.items():
        print(f"\n{name}:")
        print(content)
    
    print("\n合并处理：")
    merged_content = merge_content(user_modified_content, new_blocks, auto_detect_changes=True)
    
    print("\n合并后的文件：")
    print(merged_content)
    
    # ============================================================
    # 阶段 4: 用户修改了 AUTO 部分，系统自动检测
    # ============================================================
    print("\n【阶段 4】用户修改了 AUTO 部分，系统自动检测")
    print("-" * 70)
    
    # 用户修改了 description 部分（但标记还是 AUTO）
    user_modified_auto = """# MyProject

<!-- MOXI_AUTO:description v1 -->
## Description
This is a Python library for data processing. (用户添加了这句话)
<!-- MOXI_AUTO_END:description -->

<!-- MOXI_AUTO:installation v1 -->
## Installation
```bash
pip install myproject
```
<!-- MOXI_AUTO_END:installation -->
"""
    
    print("用户修改了 AUTO 部分（但标记还是 AUTO）：")
    print(user_modified_auto)
    
    # 系统生成新内容
    new_blocks_2 = {
        'description': '## Description\nThis is a Python library for advanced data processing.',
        'installation': '## Installation\n```bash\npip install myproject[ml]\n```',
    }
    
    print("\n系统检测到用户修改，自动转为 MANUAL：")
    merged_content_2 = merge_content(user_modified_auto, new_blocks_2, auto_detect_changes=True)
    print(merged_content_2)
    
    # ============================================================
    # 阶段 5: 用户想恢复自动更新
    # ============================================================
    print("\n【阶段 5】用户想恢复自动更新")
    print("-" * 70)
    
    manual_content = """# MyProject

<!-- MOXI_MANUAL:description v1 -->
## Description
User's custom content
<!-- MOXI_MANUAL_END:description -->
"""
    
    print("当前文件（MANUAL 模式）：")
    print(manual_content)
    
    print("\n用户手动将 MANUAL 改为 AUTO 后，下次更新：")
    # 用户手动改回 AUTO
    manual_to_auto = """# MyProject

<!-- MOXI_AUTO:description v1 -->
## Description
User's custom content
<!-- MOXI_AUTO_END:description -->
"""
    
    new_blocks_3 = {
        'description': '## Description\nAuto-generated new description',
    }
    
    merged_content_3 = merge_content(manual_to_auto, new_blocks_3, auto_detect_changes=False)
    print(merged_content_3)
    
    print("\n" + "=" * 70)
    print("演示完成！")
    print("=" * 70)


if __name__ == "__main__":
    demo()



