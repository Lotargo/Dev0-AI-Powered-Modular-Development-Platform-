import asyncio
import os
import redis.asyncio as redis
from qdrant_client import QdrantClient

async def test_redis():
    print("Testing Redis connection...")
    try:
        r = redis.from_url("redis://localhost:6379", encoding="utf-8", decode_responses=True)
        await r.set("foo", "bar")
        val = await r.get("foo")
        if val == "bar":
            print("✅ Redis: Success")
        else:
            print(f"❌ Redis: Failed (Got {val})")
        await r.close()
    except Exception as e:
        print(f"❌ Redis: Error ({e})")

def test_qdrant():
    print("Testing Qdrant connection...")
    try:
        # Qdrant client is sync by default for simple checks
        client = QdrantClient(url="http://localhost:6333")
        collections = client.get_collections()
        print(f"✅ Qdrant: Success (Collections: {collections})")
    except Exception as e:
        print(f"❌ Qdrant: Error ({e})")

async def main():
    await test_redis()
    # Run sync qdrant test
    test_qdrant()
    # Kafka test requires aiokafka or confluent-kafka which might not be installed
    # We skip kafka python test for now as we verified container status via docker ps
    # and the user didn't ask to add kafka client deps yet.

if __name__ == "__main__":
    asyncio.run(main())
