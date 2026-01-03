#!/usr/bin/env python3
"""Test script to check if nested path creation works."""

import base64
import os
import sys
from pathlib import Path
import requests

# Try to load from .env file first
def load_token_from_env():
    """Load GITHUB_TOKEN from .env file or environment variable."""
    # Try .env file first
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("GITHUB_TOKEN="):
                    token = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if token:
                        return token
    
    # Fall back to environment variable
    return os.getenv("GITHUB_TOKEN")

# Get token from environment or .env file
GITHUB_TOKEN = load_token_from_env()
REPO_OWNER = "LC0229"
REPO_NAME = "moxi"
BRANCH = "main"

def test_write_file(file_path: str, content: str) -> bool:
    """Test writing a file to a nested path."""
    print(f"\n{'=' * 70}")
    print(f"🧪 Testing: {file_path}")
    print(f"{'=' * 70}")
    
    # Encode path
    from urllib.parse import quote
    path_parts = file_path.split("/")
    encoded_parts = [quote(part, safe="") for part in path_parts]
    encoded_file_path = "/".join(encoded_parts)
    
    api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{encoded_file_path}"
    
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    
    # Check if file exists
    print(f"📋 Checking if file exists: {file_path}")
    response = requests.get(api_url, headers=headers, params={"ref": BRANCH})
    
    sha = None
    if response.status_code == 200:
        sha = response.json().get("sha")
        print(f"   ✅ File exists (SHA: {sha[:8] if sha else 'None'})")
    elif response.status_code == 404:
        print(f"   ℹ️  File does not exist, will create new")
    else:
        print(f"   ❌ Error checking file: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        return False
    
    # Check if parent directory exists (if nested)
    from pathlib import Path
    parent_dir = str(Path(file_path).parent)
    if parent_dir != "." and parent_dir:
        print(f"📁 Checking parent directory: {parent_dir}")
        parent_dir_encoded = "/".join([quote(part, safe="") for part in parent_dir.split("/")])
        parent_api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{parent_dir_encoded}"
        parent_response = requests.get(parent_api_url, headers=headers, params={"ref": BRANCH})
        
        if parent_response.status_code == 200:
            print(f"   ✅ Parent directory exists")
        elif parent_response.status_code == 404:
            print(f"   ⚠️  Parent directory does NOT exist")
            print(f"   💡 GitHub API cannot create nested paths directly")
            print(f"   💡 Need to create directory first (by creating a file in it)")
        else:
            print(f"   ❓ Unexpected status: {parent_response.status_code}")
    
    # Encode content
    content_bytes = content.encode("utf-8")
    content_base64 = base64.b64encode(content_bytes).decode("utf-8")
    
    # Prepare data
    data = {
        "message": f"test: Create {file_path}",
        "content": content_base64,
        "branch": BRANCH,
    }
    
    if sha:
        data["sha"] = sha
        print(f"📝 Updating existing file...")
    else:
        print(f"📝 Creating new file...")
    
    # Write file
    print(f"🌐 API URL: {api_url}")
    print(f"📤 Sending PUT request...")
    response = requests.put(api_url, headers=headers, json=data)
    
    if response.status_code in [200, 201]:
        print(f"   ✅ SUCCESS! File written")
        result = response.json()
        print(f"   📄 File URL: {result.get('content', {}).get('html_url', 'N/A')}")
        return True
    else:
        print(f"   ❌ FAILED: {response.status_code}")
        print(f"   Response: {response.text[:500]}")
        return False


if __name__ == "__main__":
    if not GITHUB_TOKEN or GITHUB_TOKEN.strip() == "":
        print("❌ GITHUB_TOKEN not found!")
        print()
        print("Please set it in one of these ways:")
        print("  1. Environment variable:")
        print("     export GITHUB_TOKEN='your_token_here'")
        print("  2. .env file (in project root):")
        print("     GITHUB_TOKEN=your_token_here")
        print()
        print("Get your token from: https://github.com/settings/tokens")
        print("Make sure it has 'repo' scope (not just 'public_repo')")
        sys.exit(1)
    
    # Test token validity first
    print("🔐 Testing GitHub token...")
    test_headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    test_response = requests.get("https://api.github.com/user", headers=test_headers)
    if test_response.status_code != 200:
        print(f"❌ Invalid token! Status: {test_response.status_code}")
        print(f"   Response: {test_response.text[:200]}")
        print()
        print("Possible issues:")
        print("  - Token expired or revoked")
        print("  - Token doesn't have 'repo' scope")
        print("  - Token format is incorrect")
        print()
        print("Get a new token from: https://github.com/settings/tokens")
        sys.exit(1)
    else:
        user_info = test_response.json()
        print(f"✅ Token is valid! Authenticated as: {user_info.get('login', 'Unknown')}")
        print()
    
    print("=" * 70)
    print("🧪 Testing Nested Path Creation")
    print("=" * 70)
    print(f"Repository: {REPO_OWNER}/{REPO_NAME}")
    print(f"Branch: {BRANCH}")
    print()
    
    # Test cases
    test_cases = [
        ("test_folder/test.txt", "This is a test file in test_folder/"),
        ("test_folder/nested/deep/test.txt", "This is a test file in nested/deep/"),
        (".github/workflows/test.yml", "name: Test Workflow"),
    ]
    
    results = []
    for file_path, content in test_cases:
        success = test_write_file(file_path, content)
        results.append((file_path, success))
    
    print("\n" + "=" * 70)
    print("📊 Test Results Summary")
    print("=" * 70)
    for file_path, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {file_path}")
    print()

