import asyncio
import os
import sys
from dotenv import load_dotenv

# Setup path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from project.recipes.agents.librarian import execute_async, LibrarianInput

async def seed_memory():
    print("Seeding structured memory for QR Code Task...")

    task = "Create a script that uses the 'qrcode' library to generate a QR for 'https://example.com' and saves it as qr.png."

    # This is the "Golden Lesson" we want Llama to find
    lesson_data = {
        "key_insight": "Use the qrcode library's make() function and the save() method directly on the image object.",
        "problem_summary": "Weak models fail to correctly use the qrcode library API, confusing it with reportlab or other tools.",
        "solution_code": "import qrcode\n\ndef generate_qr():\n    img = qrcode.make('https://example.com')\n    img.save('qr.png')"
    }

    # We manually invoke the store logic (simulating the agent's internal extraction)
    # by passing a fake log that "looks" like a success and forcing the librarian to store it.
    # But wait, Librarian.execute_async(mode="store") extracts from the log using LLM.
    # To ensure EXACT structure, I should probably just use QdrantManager directly here for the seed.

    from project.core.memory.qdrant_manager import get_qdrant_manager, COLLECTION_EXPERIENCES
    import uuid

    qm = get_qdrant_manager()

    qm.add_item(
        collection_name=COLLECTION_EXPERIENCES,
        text=lesson_data["key_insight"], # Embedding target
        metadata={
            "task": task,
            "outcome": "success",
            "problem_summary": lesson_data["problem_summary"],
            "solution_code": lesson_data["solution_code"],
            "is_structured": True,
            "expert_verified": True
        },
        item_id=str(uuid.uuid4())
    )

    print("Seed complete.")

if __name__ == "__main__":
    asyncio.run(seed_memory())
