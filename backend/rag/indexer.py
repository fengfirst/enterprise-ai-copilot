from pathlib import Path

import chromadb
from fastembed import TextEmbedding


KNOWLEDGE_DIR = Path("data/knowledge")
CHROMA_DIR = "data/chroma"
COLLECTION_NAME = "enterprise_knowledge"

embedding_model = TextEmbedding(
    "BAAI/bge-small-zh-v1.5"
)

client = chromadb.PersistentClient(
    path=CHROMA_DIR
)


def load_documents():
    documents = []

    for file_path in KNOWLEDGE_DIR.glob("*.txt"):
        content = file_path.read_text(encoding="utf-8")

        documents.append(
            {
                "document_id": file_path.stem,
                "file_name": file_path.name,
                "content": content,
            }
        )

    return documents


def build_index():
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME
    )

    documents = load_documents()

    ids = []
    texts = []
    metadatas = []

    for document in documents:
        ids.append(document["document_id"])
        texts.append(document["content"])
        metadatas.append(
            {
                "source": document["file_name"],
            }
        )

    embeddings = [
        vector.tolist()
        for vector in embedding_model.embed(texts)
    ]

    collection.upsert(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    print(f"Indexed documents: {len(documents)}")
    print(f"Collection count: {collection.count()}")


if __name__ == "__main__":
    build_index()