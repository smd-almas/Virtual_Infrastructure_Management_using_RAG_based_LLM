import os
import uuid
from pathlib import Path
from markdownify import markdownify as md_to_text

from embeddings import embed_and_store

# Path to the Kubernetes docs markdown directory
DOCS_DIR = Path("website/content/en/docs/concepts")

def load_markdown_files(directory: Path):
    """Yield (doc_id, text, metadata) for each markdown file."""
    for md_file in directory.rglob("*.md"):
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                markdown_content = f.read()
                plain_text = md_to_text(markdown_content)
                if not plain_text.strip():
                    continue
                doc_id = str(uuid.uuid4())
                metadata = {"source": str(md_file)}
                yield doc_id, plain_text, metadata
        except Exception as e:
            print(f"[Error reading {md_file}]: {e}")

def main():
    print("[+] Starting document embedding process...")
    file_count = 0
    for doc_id, text, metadata in load_markdown_files(DOCS_DIR):
        embed_and_store(doc_id, text, metadata)
        file_count += 1
        if file_count % 10 == 0:
            print(f"[+] Embedded {file_count} documents so far...")
    print(f"[✓] Done embedding {file_count} documents.")

if __name__ == "__main__":
    main()
