"""Debug script to inspect FAISS documents and stored content."""
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.faiss_service import get_faiss_service

def debug_faiss():
    """Show all documents and their stored content."""
    print("\n" + "="*70)
    print("FAISS DATABASE DEBUG")
    print("="*70 + "\n")

    try:
        faiss = get_faiss_service()

        # Get all documents
        docs = faiss.list_documents()

        print(f"✅ Total documents stored: {len(docs)}\n")

        if not docs:
            print("❌ No documents found in FAISS!\n")
            return

        # Show first 3 documents in detail
        for idx, doc in enumerate(docs[:3], 1):
            print(f"\n{'─'*70}")
            print(f"Document {idx}: {doc.get('source_file', 'UNKNOWN')}")
            print(f"{'─'*70}")

            print(f"  ID: {doc.get('id')}")
            print(f"  Type: {doc.get('source_type')}")
            print(f"  Timestamp: {doc.get('timestamp')}")

            # Check content_preview
            preview = doc.get('content_preview')
            if preview:
                print(f"  Preview (first 100 chars): {preview[:100]}...")
            else:
                print(f"  Preview: ❌ NOT STORED")

            # Check full_content
            full = doc.get('full_content')
            if full:
                print(f"  Full Content: ✅ STORED ({len(full)} chars)")
                print(f"  Content Preview: {full[:150]}...")
            else:
                print(f"  Full Content: ❌ NOT STORED")

        # Summary
        print(f"\n{'─'*70}")
        print("SUMMARY")
        print(f"{'─'*70}")

        full_content_count = sum(1 for d in docs if d.get('full_content'))
        preview_count = sum(1 for d in docs if d.get('content_preview'))

        print(f"Documents with preview: {preview_count}/{len(docs)}")
        print(f"Documents with full_content: {full_content_count}/{len(docs)}")

        if full_content_count == len(docs):
            print("\n✅ All documents have full_content stored! RAG should work.\n")
        else:
            print(f"\n⚠️  Only {full_content_count}/{len(docs)} documents have full_content.")
            print("   You may need to re-ingest documents.\n")

    except Exception as e:
        print(f"❌ Error: {e}\n")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_faiss()
