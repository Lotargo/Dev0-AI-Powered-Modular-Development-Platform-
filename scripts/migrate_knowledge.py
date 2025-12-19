import os
import sys
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Source: Local (default path or override)
SOURCE_PATH = os.path.join(os.getcwd(), "qdrant_storage")

# Target: Docker (from env)
TARGET_URL = os.getenv("QDRANT_URL", "http://localhost:6333")

def migrate():
    print(f"--- Qdrant Migration Tool ---")
    print(f"Source: {SOURCE_PATH}")
    print(f"Target: {TARGET_URL}")

    if not os.path.exists(SOURCE_PATH):
        print(f"Error: Local storage directory '{SOURCE_PATH}' not found.")
        print("Nothing to migrate. If you are starting fresh, run 'reindex.sh'.")
        return

    try:
        print("Connecting to local storage...")
        src_client = QdrantClient(path=SOURCE_PATH)

        print("Connecting to target server...")
        tgt_client = QdrantClient(url=TARGET_URL)

        # Test connection
        try:
            tgt_client.get_collections()
        except Exception as e:
            print(f"Error connecting to target Qdrant at {TARGET_URL}: {e}")
            print("Ensure Docker container is running via './start.sh'.")
            sys.exit(1)

        collections = src_client.get_collections().collections
        print(f"Found {len(collections)} collections in local storage.")

        for col in collections:
            name = col.name
            print(f"\nProcessing collection: {name}")

            points_count = src_client.count(name).count
            print(f"  Points: {points_count}")

            if points_count == 0:
                continue

            # Scroll and upsert
            offset = None
            total_migrated = 0

            while True:
                points, next_offset = src_client.scroll(
                    collection_name=name,
                    limit=100,
                    offset=offset,
                    with_payload=True,
                    with_vectors=True
                )

                if not points:
                    break

                # Auto-create collection on target if needed
                if total_migrated == 0 and not tgt_client.collection_exists(name):
                     # Infer vector size
                     vec = points[0].vector
                     if isinstance(vec, list):
                         dim = len(vec)
                     elif isinstance(vec, dict):
                         dim = len(next(iter(vec.values())))
                     else:
                         dim = 384

                     print(f"  Creating collection {name} on target (size={dim})...")
                     tgt_client.create_collection(
                         collection_name=name,
                         vectors_config=models.VectorParams(size=dim, distance=models.Distance.COSINE)
                     )

                tgt_client.upsert(
                    collection_name=name,
                    points=points
                )

                total_migrated += len(points)
                sys.stdout.write(f"\r  Migrated: {total_migrated}/{points_count}")
                sys.stdout.flush()

                offset = next_offset
                if offset is None:
                    break
            print(f"\n  Done.")

        print("\nMigration complete.")

    except Exception as e:
        print(f"\nCritical Error during migration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    migrate()
