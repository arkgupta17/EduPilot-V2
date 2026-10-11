import argparse
import asyncio
from pathlib import Path

from app.models.raw_page import RawPage

from app.services.crawler.crawler import WebCrawler
from app.services.processor.html_processor import HTMLProcessor
from app.services.processor.pdf_processor import PDFProcessor
from app.services.processor.document_chunker import DocumentChunker
from app.services.retrieval.retriever import Retriever


INDEX_DIR = "data/index"


async def process_website(url: str):

    crawler = WebCrawler()
    processor = HTMLProcessor()

    print(f"\nCrawling website:")
    print(url)

    await crawler.start()

    try:
        html = await crawler.crawl(url)

    finally:
        await crawler.close()

    print("Processing HTML...")

    page = RawPage(
        url=url,
        html=html
    )

    document, chunks = processor.process(
        page
    )

    print(
        f"Website chunks: {len(chunks)}"
    )

    return chunks


def process_pdf(file_path: str):

    print(
        f"\nProcessing PDF:"
    )
    print(file_path)

    processor = PDFProcessor()
    chunker = DocumentChunker()

    document = processor.process(
        file_path
    )

    chunks = chunker.create_chunks(
        document
    )

    print(
        f"PDF chunks: {len(chunks)}"
    )

    return chunks


async def main():

    parser = argparse.ArgumentParser(
        description="EduPilot knowledge base ingestion"
    )

    parser.add_argument(
        "--url",
        action="append",
        help="Website URL to crawl. Can be provided multiple times."
    )

    parser.add_argument(
        "--pdf",
        action="append",
        help="PDF file to ingest. Can be provided multiple times."
    )

    args = parser.parse_args()

    # -----------------------------------------------------
    # Validate input
    # -----------------------------------------------------

    if not args.url and not args.pdf:

        parser.error(
            "Provide at least one --url or --pdf"
        )

    all_chunks = []

    # -----------------------------------------------------
    # Process websites
    # -----------------------------------------------------

    if args.url:

        for url in args.url:

            chunks = await process_website(
                url
            )

            all_chunks.extend(
                chunks
            )

    # -----------------------------------------------------
    # Process PDFs
    # -----------------------------------------------------

    if args.pdf:

        for pdf_path in args.pdf:

            path = Path(pdf_path)

            if not path.exists():

                print(
                    f"WARNING: PDF not found: {pdf_path}"
                )

                continue

            chunks = process_pdf(
                pdf_path
            )

            all_chunks.extend(
                chunks
            )

    # -----------------------------------------------------
    # Check chunks
    # -----------------------------------------------------

    if not all_chunks:

        print(
            "\nNo chunks were created."
        )

        return

    print(
        f"\nTotal chunks for indexing: "
        f"{len(all_chunks)}"
    )

    # -----------------------------------------------------
    # Create embeddings + FAISS
    # -----------------------------------------------------

    print(
        "\nCreating embeddings and FAISS index..."
    )

    retriever = Retriever()

    retriever.index(
        all_chunks
    )

    # -----------------------------------------------------
    # Save knowledge base
    # -----------------------------------------------------

    Path(INDEX_DIR).mkdir(
        parents=True,
        exist_ok=True
    )

    retriever.save(
        INDEX_DIR
    )

    print(
        "\nKnowledge base saved."
    )

    print(
        f"Index: {INDEX_DIR}/faiss.index"
    )

    print(
        f"Chunks: {INDEX_DIR}/chunks.json"
    )

    # -----------------------------------------------------
    # Verify saved index
    # -----------------------------------------------------

    print(
        "\nLoading saved knowledge base..."
    )

    knowledge_base = Retriever()

    knowledge_base.load(
        INDEX_DIR
    )

    print(
        f"Loaded chunks: "
        f"{len(knowledge_base.chunks)}"
    )

    print(
        f"FAISS vectors: "
        f"{knowledge_base.vector_store.size()}"
    )


if __name__ == "__main__":

    asyncio.run(main())