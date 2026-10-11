import re

from app.models.document import Document
from app.models.chunk import Chunk


class DocumentChunker:

    def create_chunks(
        self,
        document: Document,
        chunk_size: int = 250,
        overlap: int = 40
    ) -> list[Chunk]:

        if overlap >= chunk_size:
            raise ValueError(
                "overlap must be smaller than chunk_size"
            )

        text = document.content.strip()

        if not text:
            return []

        # -------------------------------------------------
        # Split PDF content by page markers
        # -------------------------------------------------

        pages = re.split(
            r"(?=\[Page \d+\])",
            text
        )

        chunks = []

        for page in pages:

            page = page.strip()

            if not page:
                continue

            match = re.match(
                r"\[Page (\d+)\]",
                page
            )

            if match:

                page_number = int(
                    match.group(1)
                )

                page_text = page[
                    match.end():
                ].strip()

            else:

                page_number = None
                page_text = page

            words = page_text.split()

            if not words:
                continue

            start = 0

            while start < len(words):

                end = min(
                    start + chunk_size,
                    len(words)
                )

                chunk_text = " ".join(
                    words[start:end]
                ).strip()

                if chunk_text:

                    heading = (
                        f"Page {page_number}"
                        if page_number is not None
                        else document.title
                    )

                    chunks.append(
                        Chunk(
                            id=len(chunks),
                            document_id=document.id,
                            heading=heading,
                            text=chunk_text,
                            metadata={
                                "source_type": "pdf",
                                "source": document.url,
                                "document_title": document.title,
                                "page": page_number
                            }
                        )
                    )

                if end == len(words):
                    break

                start = end - overlap

        return chunks