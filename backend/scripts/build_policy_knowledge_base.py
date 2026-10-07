from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer


BASE_DIR = Path(__file__).resolve().parent.parent
POLICY_FILE = BASE_DIR / "knowledge" / "security_policies.txt"
CHROMA_DIR = BASE_DIR / "app" / "artifacts" / "chroma"


def load_policy_sections():
    text = POLICY_FILE.read_text(encoding="utf-8")

    sections = []
    current_title = None
    current_content = []

    for line in text.splitlines():
        line = line.strip()

        if not line:
            continue

        if line.startswith("POLICY "):
            if current_title and current_content:
                sections.append(
                    {
                        "title": current_title,
                        "content": " ".join(current_content),
                    }
                )

            current_title = line
            current_content = []

        else:
            current_content.append(line)

    if current_title and current_content:
        sections.append(
            {
                "title": current_title,
                "content": " ".join(current_content),
            }
        )

    return sections


def main():
    print("=" * 60)
    print("BOGEY-ALERT POLICY KNOWLEDGE BASE")
    print("=" * 60)

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    print("[1] Loading embedding model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    print("[2] Loading policy documents...")
    sections = load_policy_sections()

    print(f"[3] Found {len(sections)} policy sections.")

    print("[4] Initializing ChromaDB...")
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    collection = client.get_or_create_collection(
        name="security_policies"
    )

    # Clear old policy entries so rebuilding is safe.
    existing = collection.get()

    if existing["ids"]:
        collection.delete(ids=existing["ids"])

    documents = []
    ids = []
    metadatas = []

    for index, section in enumerate(sections):
        documents.append(section["content"])
        ids.append(f"policy_{index + 1}")
        metadatas.append(
            {
                "title": section["title"],
                "source": "security_policies.txt",
            }
        )

    print("[5] Creating embeddings...")
    embeddings = model.encode(
        documents,
        normalize_embeddings=True,
    ).tolist()

    print("[6] Storing policies in ChromaDB...")

    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    print()
    print("=" * 60)
    print("KNOWLEDGE BASE READY")
    print("=" * 60)
    print(f"Policies indexed : {len(documents)}")
    print(f"ChromaDB path    : {CHROMA_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()