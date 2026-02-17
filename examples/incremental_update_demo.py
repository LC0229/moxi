#!/usr/bin/env python3
"""
增量更新策略 - 基于用户修改版本继续更新
演示如何实现 INCREMENTAL 模式
"""

import re
from typing import Dict, List, Set


def parse_moxi_blocks(content: str) -> List[Dict]:
    """解析 MOXI 标记块"""
    pattern = r'<!--\s*MOXI_(AUTO|MANUAL|INCREMENTAL):(\w+)\s+v(\d+)\s*-->(.*?)<!--\s*MOXI_(AUTO|MANUAL|INCREMENTAL)_END:\2\s*-->'
    
    blocks = []
    for match in re.finditer(pattern, content, re.DOTALL):
        mode = match.group(1)
        block_name = match.group(2)
        version = match.group(3)
        block_content = match.group(4).strip()
        
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


def extract_apis(content: str) -> Set[str]:
    """从内容中提取 API 列表"""
    # 匹配 ### function_name(...) 或 ### ClassName.method_name(...)
    api_pattern = r'###\s+([\w\.]+)\([^)]*\)'
    apis = re.findall(api_pattern, content)
    return set(apis)


def extract_code_examples(content: str) -> List[str]:
    """从内容中提取代码示例"""
    code_pattern = r'```python\n(.*?)\n```'
    examples = re.findall(code_pattern, content, re.DOTALL)
    return examples


def incremental_merge(user_content: str, new_content: str, block_name: str) -> str:
    """
    增量合并：基于用户版本继续更新
    
    策略：
    1. API 列表：保留用户的，添加新的
    2. 代码示例：保留用户的，添加新的
    3. 描述性内容：如果用户修改过，保留用户版本
    4. 配置类内容：如果代码变化，更新；否则保留用户版本
    """
    user_apis = extract_apis(user_content)
    new_apis = extract_apis(new_content)
    
    user_examples = extract_code_examples(user_content)
    new_examples = extract_code_examples(new_content)
    
    # 合并 API：保留用户的，添加新的
    merged_apis = user_apis | new_apis
    
    # 合并代码示例：保留用户的，添加新的（去重）
    seen_examples = set()
    merged_examples = []
    
    # 先添加用户的
    for ex in user_examples:
        normalized = ex.strip()
        if normalized not in seen_examples:
            merged_examples.append(ex)
            seen_examples.add(normalized)
    
    # 再添加新的（如果不存在）
    for ex in new_examples:
        normalized = ex.strip()
        if normalized not in seen_examples:
            merged_examples.append(ex)
            seen_examples.add(normalized)
    
    # 重新生成内容
    result_lines = []
    
    # 提取标题（保留用户的）
    title_match = re.search(r'^##\s+(.+)$', user_content, re.MULTILINE)
    if title_match:
        result_lines.append(f"## {title_match.group(1)}")
        result_lines.append("")
    
    # 添加 API 部分
    if merged_apis:
        for api in sorted(merged_apis):
            # 从新内容中提取 API 描述
            api_pattern = rf'###\s+{re.escape(api)}\([^)]*\)\s*\n(.*?)(?=\n###|\n```|$)'
            api_match = re.search(api_pattern, new_content, re.DOTALL)
            if api_match:
                result_lines.append(f"### {api}()")
                result_lines.append(api_match.group(1).strip())
                result_lines.append("")
            else:
                # 如果新内容没有，从用户内容中提取
                api_match = re.search(api_pattern, user_content, re.DOTALL)
                if api_match:
                    result_lines.append(f"### {api}()")
                    result_lines.append(api_match.group(1).strip())
                    result_lines.append("")
    
    # 添加代码示例
    if merged_examples:
        result_lines.append("## Examples")
        result_lines.append("")
        for ex in merged_examples:
            result_lines.append("```python")
            result_lines.append(ex.strip())
            result_lines.append("```")
            result_lines.append("")
    
    return "\n".join(result_lines).strip()


def update_content(existing_content: str, new_blocks: Dict[str, str], auto_detect: bool = True) -> str:
    """
    更新内容，支持 AUTO/MANUAL/INCREMENTAL 三种模式
    
    Args:
        existing_content: 现有文件内容
        new_blocks: 新生成的块内容 {block_name: content}
        auto_detect: 是否自动检测用户修改并转为 INCREMENTAL
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
                
                # 自动检测：如果用户修改了内容，转为 INCREMENTAL（而不是 MANUAL）
                if auto_detect and new_content.strip() != block['content'].strip():
                    print(f"  🔄 检测到用户修改了 '{block_name}' 部分，转为 INCREMENTAL 模式（基于用户版本继续更新）")
                    # 增量合并
                    merged_content = incremental_merge(block['content'], new_content, block_name)
                    result_parts.append(
                        f"<!-- MOXI_INCREMENTAL:{block_name} v{current_version} -->\n"
                        f"{merged_content}\n"
                        f"<!-- MOXI_INCREMENTAL_END:{block_name} -->"
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
                result_parts.append(block['full_match'])
        
        elif mode == 'MANUAL':
            # MANUAL 模式：完全保留用户内容
            print(f"  🔒 保留用户手动维护的 '{block_name}' 部分（MANUAL 模式，不更新）")
            result_parts.append(block['full_match'])
        
        elif mode == 'INCREMENTAL':
            # INCREMENTAL 模式：基于用户版本增量更新
            if block_name in new_blocks:
                print(f"  🔄 增量更新 '{block_name}' 部分（基于用户版本继续更新）")
                new_content = new_blocks[block_name]
                merged_content = incremental_merge(block['content'], new_content, block_name)
                new_version = current_version + 1
                result_parts.append(
                    f"<!-- MOXI_INCREMENTAL:{block_name} v{new_version} -->\n"
                    f"{merged_content}\n"
                    f"<!-- MOXI_INCREMENTAL_END:{block_name} -->"
                )
            else:
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
    """演示增量更新工作流程"""
    
    print("=" * 70)
    print("增量更新策略 - 基于用户修改版本继续更新")
    print("=" * 70)
    
    # ============================================================
    # 场景 1: 用户纠正了 API 描述，希望继续自动更新
    # ============================================================
    print("\n【场景 1】用户纠正了 API 描述")
    print("-" * 70)
    
    initial_content = """# MyProject

<!-- MOXI_AUTO:api v1 -->
## API Reference
### process_data(data)
Process the input data.
<!-- MOXI_AUTO_END:api -->
"""
    
    print("初始生成（AUTO）：")
    print(initial_content)
    
    # 用户修改（纠正错误）
    user_modified = """# MyProject

<!-- MOXI_AUTO:api v1 -->
## API Reference
### process_data(data, options=None)
Process the input data with optional configuration.
<!-- MOXI_AUTO_END:api -->
"""
    
    print("\n用户修改后（纠正了参数和描述）：")
    print(user_modified)
    
    # 代码更新后，新增了 API
    new_blocks = {
        'api': """## API Reference
### process_data(data, options=None)
Process the input data with optional configuration.

### new_api(data)
New API for processing data.
"""
    }
    
    print("\n代码更新后（新增了 new_api），系统处理：")
    updated = update_content(user_modified, new_blocks, auto_detect=True)
    print(updated)
    
    # ============================================================
    # 场景 2: 用户添加了自定义示例，希望保留但继续更新
    # ============================================================
    print("\n\n【场景 2】用户添加了自定义示例")
    print("-" * 70)
    
    initial_usage = """# MyProject

<!-- MOXI_AUTO:usage v1 -->
## Usage
```python
from myproject import process_data
result = process_data(data)
```
<!-- MOXI_AUTO_END:usage -->
"""
    
    print("初始生成：")
    print(initial_usage)
    
    # 用户添加了自定义示例
    user_added_example = """# MyProject

<!-- MOXI_AUTO:usage v1 -->
## Usage
```python
from myproject import process_data
result = process_data(data)
```

### Custom Example
```python
# 用户添加的自定义示例
result = process_data(data, options={"format": "json"})
```
<!-- MOXI_AUTO_END:usage -->
"""
    
    print("\n用户添加了自定义示例：")
    print(user_added_example)
    
    # 系统生成新示例
    new_blocks_2 = {
        'usage': """## Usage
```python
from myproject import process_data
result = process_data(data)
```

### Advanced Usage
```python
result = process_data(data, options={"format": "json", "mode": "async"})
```
"""
    }
    
    print("\n系统增量更新（保留用户示例，添加新示例）：")
    updated_2 = update_content(user_added_example, new_blocks_2, auto_detect=True)
    print(updated_2)
    
    # ============================================================
    # 场景 3: INCREMENTAL 模式的持续更新
    # ============================================================
    print("\n\n【场景 3】INCREMENTAL 模式的持续更新")
    print("-" * 70)
    
    incremental_content = """# MyProject

<!-- MOXI_INCREMENTAL:api v1 -->
## API Reference
### process_data(data, options=None)
Process the input data with optional configuration.

### new_api(data)
New API for processing data.
<!-- MOXI_INCREMENTAL_END:api -->
"""
    
    print("当前内容（INCREMENTAL 模式）：")
    print(incremental_content)
    
    # 代码又更新了，新增了另一个 API
    new_blocks_3 = {
        'api': """## API Reference
### process_data(data, options=None)
Process the input data with optional configuration.

### new_api(data)
New API for processing data.

### another_new_api(data)
Another new API.
"""
    }
    
    print("\n代码再次更新（新增了 another_new_api），增量更新：")
    updated_3 = update_content(incremental_content, new_blocks_3, auto_detect=False)
    print(updated_3)
    
    print("\n" + "=" * 70)
    print("演示完成！")
    print("=" * 70)
    print("\n总结：")
    print("✅ 用户修改的内容被保留")
    print("✅ 基于用户版本继续更新（添加新的 API、示例等）")
    print("✅ 用户修改有意义，不会被完全重写")


if __name__ == "__main__":
    demo()



