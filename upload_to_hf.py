"""Upload agents_data.json, stats_data.json, and src/streamlit_app.py to HuggingFace Space."""
import os
from huggingface_hub import HfApi

token = os.environ.get("HF_TOKEN")
if not token:
    print("❌ HF_TOKEN not set — skipping upload")
    raise SystemExit(1)

api = HfApi(token=token)
REPO = "dipanshudixit/agent-hunter"

for fname in ["agents_data.json", "stats_data.json"]:
    api.upload_file(
        path_or_fileobj=fname,
        path_in_repo=f"src/{fname}",
        repo_id=REPO,
        repo_type="space",
    )
    print(f"✅ Uploaded {fname} -> src/{fname}")

api.upload_file(
    path_or_fileobj="src/streamlit_app.py",
    path_in_repo="src/streamlit_app.py",
    repo_id=REPO,
    repo_type="space",
)
print("✅ Uploaded src/streamlit_app.py")
