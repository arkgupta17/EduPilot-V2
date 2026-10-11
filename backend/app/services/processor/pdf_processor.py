from pathlib import Path

import pymupdf
import pytesseract
from PIL import Image

from app.models.document import Document

pytesseract.pytesseract.tesseract_cmd = (
    r"C:/Program Files/Tesseract-OCR/tesseract.exe"
)

class PDFProcessor:

    # =====================================================
    # PROCESS PDF
    # =====================================================

    def process(
        self,
        file_path: str
    ) -> Document:

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"PDF not found: {file_path}"
            )

        if path.suffix.lower() != ".pdf":
            raise ValueError(
                f"Expected a PDF file: {file_path}"
            )

        document = pymupdf.open(str(path))

        pages = []
        extracted_pages = 0
        ocr_pages = 0

        try:

            for page_number, page in enumerate(
                document,
                start=1
            ):

                # =================================================
                # 1. TRY NORMAL TEXT EXTRACTION
                # =================================================

                try:
                    text = page.get_text("text") or ""
                except Exception as exc:

                    print(
                        f"Warning: normal text extraction "
                        f"failed on page {page_number}: {exc}"
                    )

                    text = ""

                text = self._clean_text(
                    text
                )

                # =================================================
                # 2. FALL BACK TO OCR
                # =================================================

                if not text:

                    print(
                        f"Page {page_number}: "
                        f"no text found. Running OCR..."
                    )

                    try:

                        pixmap = page.get_pixmap(
                            matrix=pymupdf.Matrix(
                                2,
                                2
                            ),
                            alpha=False
                        )

                        image = Image.frombytes(
                            "RGB",
                            [
                                pixmap.width,
                                pixmap.height
                            ],
                            pixmap.samples
                        )

                        text = pytesseract.image_to_string(
                            image
                        )

                        text = self._clean_text(
                            text
                        )

                        if text:
                            ocr_pages += 1

                    except Exception as exc:

                        print(
                            f"Warning: OCR failed on "
                            f"page {page_number}: {exc}"
                        )

                        text = ""

                else:

                    extracted_pages += 1

                # =================================================
                # 3. STORE PAGE
                # =================================================

                if text:

                    pages.append(
                        f"[Page {page_number}]\n"
                        f"{text}"
                    )

        finally:

            document.close()

        # =====================================================
        # 4. COMBINE CONTENT
        # =====================================================

        content = "\n\n".join(
            pages
        )

        # =====================================================
        # 5. RETURN DOCUMENT
        # =====================================================

        return Document(

            id=str(
                path.resolve()
            ),

            title=path.stem,

            source_type="pdf",

            url=str(
                path.resolve()
            ),

            content=content,

            metadata={

                "source": str(
                    path.resolve()
                ),

                "source_type": "pdf",

                "document_title": path.stem,

                "pages": len(
                    pages
                ),

                "total_pages": (
                    len(pages)
                    if pages
                    else 0
                ),

                "extracted_pages": (
                    extracted_pages
                ),

                "ocr_pages": (
                    ocr_pages
                )
            }
        )

    # =====================================================
    # TEXT CLEANING
    # =====================================================

    @staticmethod
    def _clean_text(
        text: str
    ) -> str:

        if not text:
            return ""

        text = text.replace(
            "\x00",
            " "
        )

        lines = []

        for line in text.splitlines():

            line = " ".join(
                line.split()
            ).strip()

            if line:
                lines.append(
                    line
                )

        return "\n".join(
            lines
        )