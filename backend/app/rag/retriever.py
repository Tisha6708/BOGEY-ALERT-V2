from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer


BASE_DIR = Path(__file__).resolve().parent.parent

CHROMA_DIR = (
    BASE_DIR
    / "artifacts"
    / "chroma"
)

COLLECTION_NAME = "security_policies"


class PolicyRetriever:
    """
    Retrieves relevant organizational security policies
    for a detected insider-threat event.
    """

    def __init__(self):
        self.embedding_model = SentenceTransformer(
            "all-MiniLM-L6-v2"
        )

        self.client = chromadb.PersistentClient(
            path=str(CHROMA_DIR)
        )

        self.collection = self.client.get_collection(
            name=COLLECTION_NAME
        )

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[dict]:
        """
        Retrieve the most relevant security policies.
        """

        if not query.strip():
            return []

        query_embedding = self.embedding_model.encode(
            query,
            normalize_embeddings=True,
        ).tolist()

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        retrieved = []

        for document, metadata, distance in zip(
            documents,
            metadatas,
            distances,
        ):
            retrieved.append(
                {
                    "title": metadata.get(
                        "title",
                        "Unknown Policy",
                    ),
                    "source": metadata.get(
                        "source",
                        "security_policies.txt",
                    ),
                    "content": document,
                    "distance": float(distance),
                }
            )

        return retrieved


if __name__ == "__main__":
    retriever = PolicyRetriever()

    query = """
    Employee performed mass deletion of sensitive files,
    unusually high data volume, and behavior significantly
    deviated from the employee baseline.
    """

    results = retriever.retrieve(
        query=query,
        top_k=4,
    )

    print("=" * 60)
    print("BOGEY-ALERT RAG RETRIEVAL TEST")
    print("=" * 60)

    for index, result in enumerate(results, start=1):
        print(f"\n[{index}] {result['title']}")
        print(f"Distance: {result['distance']:.4f}")
        print(f"Content: {result['content']}")

    print("\n" + "=" * 60)