import chromadb
from fastembed import TextEmbedding


CHROMA_DIR = "data/chroma"
COLLECTION_NAME = "enterprise_knowledge"

embedding_model = TextEmbedding(
    "BAAI/bge-small-zh-v1.5"
)

client = chromadb.PersistentClient(
    path=CHROMA_DIR
)

collection = client.get_collection(
    COLLECTION_NAME
)


def search_knowledge(
    query: str,
    top_k: int = 3,
    distance_threshold: float = 0.75,
) -> dict:
    query_embedding = list(
        embedding_model.embed([query])
    )[0].tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
    )

    documents = results["documents"][0]
    distances = results["distances"][0]
    metadatas = results["metadatas"][0]
    ids = results["ids"][0]

    retrieved = []

    for document_id, document, distance, metadata in zip(
        ids,
        documents,
        distances,
        metadatas,
    ):
        if distance > distance_threshold:
            continue

        retrieved.append(
            {
                "document_id": document_id,
                "content": document,
                "distance": distance,
                "metadata": metadata,
            }
        )

    return {
        "found": len(retrieved) > 0,
        "results": retrieved,
    }