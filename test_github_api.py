#!/usr/bin/env python3
"""Test script to diagnose GitHub API issue with .github directory."""

import base64
import os
import sys
from pathlib import Path
import requests
from urllib.parse import quote

# Load token from .env or environment
def load_token():
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("GITHUB_TOKEN="):
                    token = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if token:
                        return token
    return os.getenv("GITHUB_TOKEN")

GITHUB_TOKEN = load_token()
REPO_OWNER = "LC0229"
REPO_NAME = "moxi"
BRANCH = "main"

if not GITHUB_TOKEN:
    print("❌ GITHUB_TOKEN not found!")
    sys.exit(1)

headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}

print("=" * 70)
print("🔍 GitHub API 诊断测试")
print("=" * 70)
print()

# Test 1: Check if directory exists
print("测试 1: 检查目录是否存在")
print("-" * 70)
dir_path = ".github/workflows"
dir_encoded = "/".join([quote(part, safe="") for part in dir_path.split("/")])
dir_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{dir_encoded}"
print(f"URL: {dir_url}")
response = requests.get(dir_url, headers=headers, params={"ref": BRANCH})
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    if isinstance(data, list):
        print(f"✅ 目录存在，包含 {len(data)} 个文件:")
        for item in data:
            print(f"   - {item.get('name')} ({item.get('type')})")
    else:
        print(f"⚠️  返回的是对象，不是数组: {data.get('name', 'Unknown')}")
else:
    print(f"❌ 目录不存在或无法访问")
    print(f"Response: {response.text[:200]}")
print()

# Test 2: Check if file exists
print("测试 2: 检查文件是否存在")
print("-" * 70)
file_path = ".github/workflows/auto-generate-docs.yml"
file_encoded = "/".join([quote(part, safe="") for part in file_path.split("/")])
file_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{file_encoded}"
print(f"URL: {file_url}")
response = requests.get(file_url, headers=headers, params={"ref": BRANCH})
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"✅ 文件存在")
    print(f"   SHA: {data.get('sha', 'N/A')[:8]}")
    print(f"   Size: {data.get('size', 'N/A')} bytes")
elif response.status_code == 404:
    print(f"✅ 文件不存在（可以创建）")
else:
    print(f"❌ 错误: {response.text[:200]}")
print()

# Test 3: Try to create file
print("测试 3: 尝试创建文件")
print("-" * 70)
content = "name: Test Workflow\non: [push]\n"
content_base64 = base64.b64encode(content.encode("utf-8")).decode("utf-8")

data = {
    "message": "test: Create auto-generate-docs.yml",
    "content": content_base64,
    "branch": BRANCH,
}

print(f"URL: {file_url}")
print(f"Branch: {BRANCH}")
print(f"Content length: {len(content)} bytes")
response = requests.put(file_url, headers=headers, json=data)
print(f"Status: {response.status_code}")

if response.status_code in [200, 201]:
    result = response.json()
    print(f"✅ 文件创建成功！")
    print(f"   Commit: {result.get('commit', {}).get('sha', 'N/A')[:8]}")
    print(f"   URL: {result.get('content', {}).get('html_url', 'N/A')}")
else:
    print(f"❌ 文件创建失败")
    error_json = response.json() if response.text else {}
    print(f"   Message: {error_json.get('message', 'Unknown error')}")
    print(f"   Full response: {response.text[:500]}")
print()

# Test 4: Check branch
print("测试 4: 检查分支")
print("-" * 70)
branch_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/branches/{BRANCH}"
response = requests.get(branch_url, headers=headers)
print(f"URL: {branch_url}")
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"✅ 分支存在")
    print(f"   Name: {data.get('name', 'N/A')}")
    print(f"   SHA: {data.get('commit', {}).get('sha', 'N/A')[:8]}")
else:
    print(f"❌ 分支不存在或无法访问")
    print(f"Response: {response.text[:200]}")
print()

print("=" * 70)
print("📊 诊断完成")
print("=" * 70)

