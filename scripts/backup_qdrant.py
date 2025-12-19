import os
import sys
import httpx

# We read QDRANT_URL or default
# Note: If running from host, localhost:6333 is correct (mapped port)
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
BACKUP_DIR = sys.argv[1]

print(f"Connecting to Qdrant at {QDRANT_URL}")

try:
    # 1. Get Collections
    resp = httpx.get(f"{QDRANT_URL}/collections")
    resp.raise_for_status()
    collections = resp.json().get("result", {}).get("collections", [])

    if not collections:
        print("No collections found to backup.")

    for col in collections:
        name = col["name"]
        print(f"Snapshotting collection: {name}")

        # 2. Create Snapshot
        # This triggers a server-side snapshot
        snap_resp = httpx.post(f"{QDRANT_URL}/collections/{name}/snapshots")
        snap_resp.raise_for_status()
        snapshot_name = snap_resp.json()["result"]["name"]

        # 3. Download
        # The snapshot is stored on the server. We download it to local backup dir.
        download_url = f"{QDRANT_URL}/collections/{name}/snapshots/{snapshot_name}"
        print(f"Downloading {snapshot_name}...")

        # Use simple stream download
        save_path = os.path.join(BACKUP_DIR, f"{name}.snapshot")
        with open(save_path, "wb") as f:
            with httpx.stream("GET", download_url, timeout=60.0) as r:
                for chunk in r.iter_bytes():
                    f.write(chunk)

        print(f"Saved to {save_path}")

except Exception as e:
    print(f"Error backing up Qdrant: {e}")
    sys.exit(1)
