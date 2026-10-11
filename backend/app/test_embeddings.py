from app.services.retrieval.embedder import Embedder


def main():

    embedder = Embedder()

    texts = [
        "The programme duration is 15 months.",
        "The curriculum includes AI and agentic systems.",
        "The programme includes real-world projects."
    ]

    embeddings = embedder.embed(texts)

    print("Number of embeddings:", len(embeddings))
    print("Vector dimension:", embeddings.shape[1])
    print("Shape:", embeddings.shape)


if __name__ == "__main__":
    main()