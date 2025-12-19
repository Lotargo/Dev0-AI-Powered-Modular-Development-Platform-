import sys
import os
import uuid
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from project.core.memory.qdrant_manager import get_qdrant_manager, COLLECTION_EXPERIENCES

def main():
    qm = get_qdrant_manager()
    lesson = """
**CRITICAL REPORTLAB RULE:**
To generate barcodes in ReportLab:
1. DO NOT import `reportlab.Barcode` (it does not exist).
2. DO NOT import `barcode` (this is a different library).
3. YOU MUST USE: `from reportlab.graphics.barcode import code128`.
4. Ensure `reportlab` is installed. No other barcode libraries are needed.
"""
    print(f"Injecting lesson:\n{lesson}")

    qm.add_item(
        collection_name=COLLECTION_EXPERIENCES,
        text=lesson,
        metadata={"source": "Expert Manual Injection", "topic": "reportlab barcode"},
        item_id=str(uuid.uuid4())
    )
    print("Done.")

if __name__ == "__main__":
    main()
