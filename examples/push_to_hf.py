"""
Push JSONL data to HuggingFace.
Usage: python push_to_hf.py <path_to_jsonl> <repo_id>
"""

import sys
from pathlib import Path

from huggingface_hub import HfApi, create_repo


def push_to_hf(jsonl_path, repo_id):
    """Push JSONL file to HuggingFace dataset repo."""

    # Check file exists
    jsonl_path = Path(jsonl_path)
    if not jsonl_path.exists():
        print(f"Error: {jsonl_path} not found")
        return

    # Count records
    with open(jsonl_path) as f:
        lines = f.readlines()
    print(f"Found {len(lines)} records")

    # Create repo
    api = HfApi()
    try:
        create_repo(repo_id, repo_type="dataset", exist_ok=True)
        print(f"✓ Repo created: {repo_id}")
    except Exception as e:
        print(f"Error: {e}")
        return

    # Upload file
    try:
        api.upload_file(
            path_or_fileobj=str(jsonl_path),
            path_in_repo="data/train.jsonl",
            repo_id=repo_id,
            repo_type="dataset",
        )
        print(f"✓ Uploaded")
        print(f"View: https://huggingface.co/datasets/{repo_id}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python push_to_hf.py <jsonl_path> <repo_id>")
        print("Example: python push_to_hf.py pidgin_data/data.jsonl Aletheia-ng/pidgin")
        sys.exit(1)

    push_to_hf(sys.argv[1], sys.argv[2])
