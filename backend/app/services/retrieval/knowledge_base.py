from .retriever import Retriever


class KnowledgeBase:

    def __init__(self, index_path: str = "data/index"):

        self.retriever = Retriever()

        self.retriever.load(index_path)

    def search(self, query: str, top_k: int = 5):

        return self.retriever.retrieve(
            query,
            top_k
        )