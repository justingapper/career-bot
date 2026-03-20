import os
from pathlib import Path

from openai import OpenAI

DOCS_DIR = Path("docs")
VECTOR_STORE_NAME = os.getenv("VECTOR_STORE_NAME", "career-bot-kb")
client = OpenAI()


def main() -> None:
    doc_paths = sorted(
        [p for p in DOCS_DIR.iterdir() if p.is_file() and p.suffix.lower() in {".md", ".txt", ".pdf", ".docx", ".json"}]
    )

    if not doc_paths:
        raise RuntimeError(f"No documents found in {DOCS_DIR.resolve()}")

    vector_store = client.vector_stores.create(name=VECTOR_STORE_NAME)
    print(f"Created vector store: {vector_store.id}")

    for path in doc_paths:
        print(f"Uploading {path.name} ...")
        with path.open("rb") as f:
            client.vector_stores.files.upload_and_poll(
                vector_store_id=vector_store.id,
                file=f,
            )

    print("Done.")
    print("Set this in your environment:")
    print(f"OPENAI_VECTOR_STORE_ID={vector_store.id}")


if __name__ == "__main__":
    main()
