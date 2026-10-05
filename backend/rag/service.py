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

def normalize_text(text: str) -> str:
    if not text:
        return ""

    return (
        str(text)
        .replace(" ", "")
        .replace("\n", "")
        .replace("\r", "")
        .replace("　", "")
    )


def lexical_score(query: str, document: str) -> float:
    """
    计算 query 的字符 Bigram 在 document 中的覆盖率。

    与 Jaccard 不同：
    只关心「用户查询中的文本，有多少能够在候选文档中找到」。
    """

    query = normalize_text(query)
    document = normalize_text(document)

    if len(query) < 2:
        return 0.0

    query_bigrams = {
        query[i:i + 2]
        for i in range(len(query) - 1)
    }

    document_bigrams = {
        document[i:i + 2]
        for i in range(len(document) - 1)
    }

    if not query_bigrams:
        return 0.0

    matched = query_bigrams & document_bigrams

    return len(matched) / len(query_bigrams)


def search_knowledge(
    query: str,
    top_k: int = 3,
    distance_threshold: float = 0.85,
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

        lexical = lexical_score(query, document)

        # distance 越小越好，因此转换成 0~1 的 embedding score
        embedding_score = 1 / (1 + distance)

        # 综合排序：
        # embedding 保留语义能力
        # lexical 提升精确文本匹配能力
        rerank_score = (
            0.65 * embedding_score
            + 0.35 * lexical
        )

        retrieved.append(
            {
                "document_id": document_id,
                "content": document,
                "distance": distance,
                "metadata": metadata,
                "lexical_score": lexical,
                "embedding_score": embedding_score,
                "rerank_score": rerank_score,
            }
        )

    retrieved.sort(
        key=lambda item: item["rerank_score"],
        reverse=True,
    )

    return {
        "found": len(retrieved) > 0,
        "results": retrieved,
    }