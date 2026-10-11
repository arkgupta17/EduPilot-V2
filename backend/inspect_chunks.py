from app.services.retrieval.retriever import Retriever

retriever = Retriever()
retriever.load("data/index")

document_id = "de01d5d7851142b4a3863189848a5b65"

for chunk in retriever.chunks:
    if str(chunk.document_id) == document_id:
        print("\n" + "=" * 80)
        print("HEADING:", chunk.heading)
        print(chunk.text[:1000])