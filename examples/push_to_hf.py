"""
Push JSONL data to HuggingFace.
Usage: python push_to_hf.py <path_to_jsonl> <repo_id> [filename]
"""

import sys
from datetime import datetime
from pathlib import Path

from huggingface_hub import HfApi, create_repo


def push_to_hf(jsonl_path, repo_id, filename=None):
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

    # Generate filename if not provided
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"train_{timestamp}.jsonl"

    # Ensure .jsonl extension
    if not filename.endswith(".jsonl"):
        filename += ".jsonl"

    path_in_repo = f"data/{filename}"

    # Create repo
    api = HfApi()
    try:
        create_repo(repo_id, repo_type="dataset", exist_ok=True)
        print(f"✓ Repo ready: {repo_id}")
    except Exception as e:
        print(f"Error: {e}")
        return

    # Upload file
    try:
        api.upload_file(
            path_or_fileobj=str(jsonl_path),
            path_in_repo=path_in_repo,
            repo_id=repo_id,
            repo_type="dataset",
        )
        print(f"✓ Uploaded to: {path_in_repo}")
        print(f"View: https://huggingface.co/datasets/{repo_id}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python push_to_hf.py <jsonl_path> <repo_id> [filename]")
        print()
        print("Examples:")
        print("  # Auto-generate timestamped filename")
        print("  python push_to_hf.py pidgin_data/data.jsonl Aletheia-ng/pidgin")
        print()
        print("  # Specify custom filename")
        print(
            "  python push_to_hf.py pidgin_data/data.jsonl Aletheia-ng/pidgin batch_001"
        )
        sys.exit(1)

    jsonl_path = sys.argv[1]
    repo_id = sys.argv[2]
    filename = sys.argv[3] if len(sys.argv) > 3 else None

    push_to_hf(jsonl_path, repo_id, filename)
