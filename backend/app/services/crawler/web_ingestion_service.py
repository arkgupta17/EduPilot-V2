from pathlib import Path
import shutil
import tempfile
import uuid

from urllib.request import Request, urlopen

from app.models.raw_page import RawPage

from app.services.crawler.crawler import WebCrawler
from app.services.processor.html_processor import HTMLProcessor
from app.services.processor.pdf_processor import PDFProcessor
from app.services.processor.document_chunker import DocumentChunker
from app.services.retrieval.retriever import Retriever
from urllib.parse import urlparse


INDEX_DIR = "data/index"


class WebIngestionService:


    def __init__(
        self,
        max_pages=25,
        max_depth=2,
    ):

        self.max_pages = max_pages
        self.max_depth = max_depth

        self.html_processor = HTMLProcessor()
        self.pdf_processor = PDFProcessor()
        self.chunker = DocumentChunker()

    # =====================================================
    # MAIN INGESTION
    # =====================================================

    async def ingest(
        self,
        url: str,
    ) -> dict:

        # -------------------------------------------------
        # One source_id for the entire website
        # -------------------------------------------------

        source_id = uuid.uuid4().hex

        crawler = WebCrawler(
            max_pages=self.max_pages,
            max_depth=self.max_depth,
        )

        all_chunks = []
        processed_documents = []

        try:

            await crawler.start()

            pages = await crawler.crawl(
                url
            )

            if not pages:

                raise ValueError(
                    "No readable webpages or documents were found."
                )

            # =================================================
            # PROCESS EVERY CRAWLED ITEM
            # =================================================

            for page_data in pages:

                page_type = page_data.get(
                    "type",
                    "html",
                )

                page_url = page_data["url"]

                # =================================================
                # HTML
                # =================================================

                if page_type == "html":

                    raw_page = RawPage(
                        url=page_url,
                        html=page_data["html"],
                    )

                    try:

                        document, chunks = (
                            self.html_processor.process(
                                raw_page
                            )
                        )

                    except Exception as exc:

                        import traceback

                        print(
                            "\n========== HTML PROCESSING ERROR =========="
                        )

                        print(
                            "URL:",
                            page_url,
                        )

                        print(
                            "Exception type:",
                            type(exc).__name__,
                        )

                        print(
                            "Exception:",
                            repr(exc),
                        )

                        traceback.print_exc()

                        print(
                            "===========================================\n"
                        )

                        continue

                # =================================================
                # PDF
                # =================================================

                elif page_type == "pdf":

                    try:

                        document, chunks = (
                            self._process_pdf_url(
                                page_url
                            )
                        )

                    except Exception as exc:

                        import traceback

                        print(
                            "\n========== PDF PROCESSING ERROR =========="
                        )

                        print(
                            "URL:",
                            page_url,
                        )

                        print(
                            "Exception type:",
                            type(exc).__name__,
                        )

                        print(
                            "Exception:",
                            repr(exc),
                        )

                        traceback.print_exc()

                        print(
                            "==========================================\n"
                        )

                        # One bad PDF should NOT
                        # kill the entire website.
                        continue

                else:

                    continue

                # =================================================
                # NO CHUNKS
                # =================================================

                if not chunks:
                    continue

                # =================================================
                # CREATE UNIQUE DOCUMENT ID
                # =================================================

                document_id = uuid.uuid4().hex

                document.id = document_id

                # =================================================
                # DOCUMENT METADATA
                # =================================================

                document.metadata.update(
                    {
                        "source_id": source_id,
                        "document_id": document_id,
                        "source_type": page_type,
                        "source": page_url,
                        "source_url": page_url,
                        "document_title": document.title,
                    }
                )

                # =================================================
                # CHUNK METADATA
                # =================================================

                for chunk in chunks:

                    chunk.document_id = document_id

                    if chunk.metadata is None:
                        chunk.metadata = {}

                    chunk.metadata.update(
                        {
                            "source_type": page_type,
                            "source": page_url,
                            "source_url": page_url,
                            "source_id": source_id,
                            "document_id": document_id,
                            "document_title": document.title,
                        }
                    )

                    all_chunks.append(
                        chunk
                    )

                # =================================================
                # DOCUMENT INFORMATION
                # =================================================

                processed_documents.append(
                    {
                        "document_id": document_id,
                        "url": page_url,
                        "title": document.title,
                        "type": page_type,
                        "chunks": len(chunks),
                    }
                )

        finally:

            await crawler.close()

        # =========================================================
        # CHECK
        # =========================================================

        if not all_chunks:

            raise ValueError(
                "The website was crawled, but no readable "
                "content could be extracted."
            )

        # =========================================================
        # LOAD EXISTING KNOWLEDGE BASE
        # =========================================================

        try:

            existing_retriever = Retriever()

            existing_retriever.load(
                INDEX_DIR
            )

            existing_chunks = list(
                existing_retriever.chunks
            )

        except Exception as exc:

            print(
                "Existing knowledge base could not be loaded:",
                exc,
            )

            existing_chunks = []

        # =========================================================
        # UNIQUE CHUNK IDS
        # =========================================================

        start_id = len(
            existing_chunks
        )

        for index, chunk in enumerate(
            all_chunks
        ):

            chunk.id = (
                start_id + index
            )

        combined_chunks = (
            existing_chunks
            + all_chunks
        )

        # =========================================================
        # CREATE FAISS INDEX
        # =========================================================

        retriever = Retriever()

        retriever.index(
            combined_chunks
        )

        Path(
            INDEX_DIR
        ).mkdir(
            parents=True,
            exist_ok=True,
        )

        retriever.save(
            INDEX_DIR
        )

        # =========================================================
        # VERIFY SAVED INDEX
        # =========================================================

        verification = Retriever()

        verification.load(
            INDEX_DIR
        )

        indexed_chunks = [
            chunk
            for chunk in verification.chunks
            if str(
                chunk.metadata.get(
                    "source_id",
                    "",
                )
            )
            == str(source_id)
        ]

        if not indexed_chunks:

            raise RuntimeError(
                "Website content was not found "
                "in the saved knowledge base."
            )

        # =========================================================
        # SUCCESS
        # =========================================================

        html_documents = [
            document
            for document in processed_documents
            if document["type"] == "html"
        ]

        pdf_documents = [
            document
            for document in processed_documents
            if document["type"] == "pdf"
        ]

        return {
            "source_id": source_id,
            "url": url,

            "pages_crawled": len(
                html_documents
            ),

            "documents_processed": len(
                processed_documents
            ),

            "pdfs_processed": len(
                pdf_documents
            ),

            "chunks": len(
                indexed_chunks
            ),

            "total_indexed_chunks": len(
                verification.chunks
            ),

            "pages": processed_documents,

            "status": "indexed",
        }

    # =====================================================
    # DOWNLOAD + PROCESS LINKED PDF
    # =====================================================

    def _process_pdf_url(
        self,
        pdf_url: str,
    ):

        print(
            "\nDownloading linked PDF:"
        )

        print(
            pdf_url
        )

        # =================================================
        # DOWNLOAD
        # =================================================

        request = Request(
            pdf_url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/131.0.0.0 Safari/537.36"
                )
            },
        )

        with urlopen(request, timeout=30) as response:
            response_content = response.read()
            response_url = response.geturl()
            response_headers = response.headers

        # =================================================
        # VERIFY PDF
        # =================================================

        content_type = (
            response_headers
            .get(
                "content-type",
                "",
            )
            .lower()
        )

        final_url = response_url

        is_pdf = (
            "application/pdf"
            in content_type
            or WebCrawler.is_pdf_url(
                final_url
            )
            or WebCrawler.is_pdf_url(
                pdf_url
            )
        )

        if not is_pdf:

            raise ValueError(
                "URL did not return a PDF: "
                f"{pdf_url}"
            )

        if not response_content:

            raise ValueError(
                f"Downloaded PDF is empty: {pdf_url}"
            )

        # =================================================
        # TEMPORARY FILE
        # =================================================

        temp_dir = Path(
            tempfile.mkdtemp(
                prefix="edupilot_pdf_"
            )
        )

        try:

            parsed_url = urlparse(
                final_url
            )

            filename = Path(
                parsed_url.path
            ).name

            if not filename:

                filename = "document.pdf"

            if not filename.lower().endswith(
                ".pdf"
            ):

                filename += ".pdf"

            file_path = (
                temp_dir / filename
            )

            file_path.write_bytes(
                response_content
            )

            print(
                f"Saved temporary PDF: {file_path}"
            )

            # =================================================
            # PDF PROCESSOR
            # =================================================

            document = (
                self.pdf_processor.process(
                    str(file_path)
                )
            )

            # =================================================
            # CHUNKER
            # =================================================

            chunks = (
                self.chunker.create_chunks(
                    document
                )
            )

            print(
                f"PDF chunks: {len(chunks)}"
            )

            # =================================================
            # REPLACE LOCAL PATH WITH REAL URL
            # =================================================

            document.url = pdf_url

            document.metadata.update(
                {
                    "source": pdf_url,
                    "source_url": pdf_url,
                    "source_type": "pdf",
                    "filename": filename,
                    "linked_document": True,
                    "uploaded": False,
                }
            )

            return (
                document,
                chunks,
            )

        finally:

            # =================================================
            # DELETE TEMPORARY FILE
            # =================================================

            shutil.rmtree(
                temp_dir,
                ignore_errors=True,
            )