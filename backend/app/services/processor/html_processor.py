import re

from bs4 import BeautifulSoup

from app.models.document import Document
from app.models.chunk import Chunk
from app.models.raw_page import RawPage


class HTMLProcessor:

    def process(self, page: RawPage):

        soup = BeautifulSoup(
            page.html,
            "lxml"
        )

        # =====================================================
        # 1. Remove elements that should not become knowledge
        # =====================================================

        for tag in soup([
            "script",
            "style",
            "noscript",
            "iframe",
            "svg",
            "canvas",
            "footer",
            "nav",
            "header",
            "aside",
            "form",
            "button"
        ]):

            tag.decompose()

        # =====================================================
        # 2. Remove common UI / popup elements
        # =====================================================

        selectors = [
            "[class*='cookie']",
            "[class*='popup']",
            "[class*='modal']",
            "[class*='navbar']",
            "[class*='menu']",
            "[class*='footer']",
            "[class*='header']",
            "[class*='sidebar']",
            "[class*='breadcrumb']",
            "[id*='cookie']",
            "[id*='popup']",
            "[id*='modal']",
            "[id*='navbar']",
            "[id*='menu']",
            "[id*='footer']",
            "[id*='header']",
            "[id*='sidebar']"
        ]

        for selector in selectors:

            for element in soup.select(
                selector
            ):

                element.decompose()

        # =====================================================
        # 3. Find the main content
        #
        # Generic strategy:
        #
        # main -> article -> largest content container -> body
        # =====================================================

        main = soup.find("main")

        if not main:

            main = soup.find("article")

        if not main:

            main = self._find_largest_content(
                soup
            )

        if not main:

            main = soup.body

        if not main:

            return self._empty_document(
                page
            )

        # =====================================================
        # 4. Remove hidden elements
        # =====================================================

        for element in main.select(
            ".hide, .hidden, [hidden], "
            "[aria-hidden='true']"
        ):

            element.decompose()

        # =====================================================
        # 5. Extract title
        # =====================================================

        title = "Untitled"

        if soup.title:

            title_text = soup.title.get_text(
                " ",
                strip=True
            )

            if title_text:

                title = title_text

        # =====================================================
        # 6. Create document
        # =====================================================

        document = Document(
            id=page.url,
            title=title,
            source_type="website",
            url=page.url,
            content="",
            metadata={
                "source": page.url,
                "source_type": "website",
                "document_title": title
            }
        )

        # =====================================================
        # 7. Create semantic chunks
        #
        # Prefer headings when available.
        # =====================================================

        chunks = self._create_heading_chunks(
            main,
            document
        )

        # =====================================================
        # 8. Fallback for pages without headings
        # =====================================================

        if not chunks:

            chunks = self._create_fallback_chunks(
                main,
                document
            )

        # =====================================================
        # 9. Store cleaned document text
        # =====================================================

        document.content = self._clean_text(
            main.get_text(
                "\n",
                strip=True
            )
        )

        return document, chunks

    # =========================================================
    # FIND LARGEST CONTENT CONTAINER
    # =========================================================

    def _find_largest_content(
        self,
        soup: BeautifulSoup
    ):

        candidates = soup.find_all(
            ["div", "section"]
        )

        if not candidates:

            return None

        best_element = None
        best_score = 0

        for element in candidates:

            text = element.get_text(
                " ",
                strip=True
            )

            if not text:

                continue

            # Number of useful text elements
            paragraphs = len(
                element.find_all(
                    ["p", "li"]
                )
            )

            headings = len(
                element.find_all(
                    ["h1", "h2", "h3"]
                )
            )

            text_length = len(text)

            # Simple content score
            score = (
                text_length
                +
                paragraphs * 100
                +
                headings * 200
            )

            if score > best_score:

                best_score = score
                best_element = element

        return best_element

    # =========================================================
    # HEADING-BASED CHUNKS
    # =========================================================

    def _create_heading_chunks(
        self,
        main,
        document
    ):

        headings = main.find_all(
            ["h1", "h2", "h3"]
        )

        chunks = []

        chunk_id = 0

        for heading in headings:

            heading_text = heading.get_text(
                " ",
                strip=True
            )

            if not heading_text:

                continue

            section_text = []

            for element in heading.find_all_next():

                if element is heading:

                    continue

                # Stop at the next heading
                if element.name in [
                    "h1",
                    "h2",
                    "h3"
                ]:

                    break

                if element.name in [
                    "script",
                    "style",
                    "noscript",
                    "svg"
                ]:

                    continue

                if element.name in [
                    "p",
                    "li"
                ]:

                    text = element.get_text(
                        " ",
                        strip=True
                    )

                    text = self._clean_text(
                        text
                    )

                    if text:

                        section_text.append(
                            text
                        )

            # Remove duplicate lines
            cleaned = []

            for text in section_text:

                if text not in cleaned:

                    cleaned.append(text)

            if not cleaned:

                continue

            chunk_text = "\n".join(
                cleaned
            )

            chunks.append(
                Chunk(
                    id=chunk_id,
                    document_id=document.id,
                    heading=heading_text,
                    text=chunk_text,
                    metadata={
                        "source_type": "website",
                        "source": document.url,
                        "document_title": document.title
                    }
                )
            )

            chunk_id += 1

        return chunks

    # =========================================================
    # FALLBACK CHUNKS
    # =========================================================

    def _create_fallback_chunks(
        self,
        main,
        document,
        chunk_size=250
    ):

        text = self._clean_text(
            main.get_text(
                " ",
                strip=True
            )
        )

        if not text:

            return []

        words = text.split()

        chunks = []

        start = 0

        chunk_id = 0

        while start < len(words):

            end = min(
                start + chunk_size,
                len(words)
            )

            chunk_text = " ".join(
                words[start:end]
            )

            if chunk_text:

                chunks.append(
                    Chunk(
                        id=chunk_id,
                        document_id=document.id,
                        heading=document.title,
                        text=chunk_text,
                        metadata={
                            "source_type": "website",
                            "source": document.url,
                            "document_title": document.title
                        }
                    )
                )

                chunk_id += 1

            start = end

        return chunks

    # =========================================================
    # TEXT CLEANING
    # =========================================================

    @staticmethod
    def _clean_text(
        text: str
    ):

        text = re.sub(
            r"\s+",
            " ",
            text
        )

        return text.strip()

    # =========================================================
    # EMPTY DOCUMENT
    # =========================================================

    @staticmethod
    def _empty_document(
        page: RawPage
    ):

        document = Document(
            id=page.url,
            title="Untitled",
            source_type="website",
            url=page.url,
            content="",
            metadata={
                "source": page.url,
                "source_type": "website",
                "document_title": "Untitled"
            }
        )

        return document, []