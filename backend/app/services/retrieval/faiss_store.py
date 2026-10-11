import faiss
import numpy as np


class VectorStore:

    def __init__(self, dimension: int):
        self.index = faiss.IndexFlatIP(dimension)

    def add(self, embeddings):
        embeddings = np.asarray(
            embeddings,
            dtype="float32"
        )

        self.index.add(embeddings)

    def search(self, query_embedding, k=5):
        query_embedding = np.asarray(
            [query_embedding],
            dtype="float32"
        )

        scores, indices = self.index.search(
            query_embedding,
            k
        )

        return scores[0], indices[0]

    def save(self, path: str):
        faiss.write_index(self.index, path)

    def load(self, path: str):
        self.index = faiss.read_index(path)

    def size(self):
        return self.index.ntotal