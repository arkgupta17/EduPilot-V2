from pathlib import Path
import shutil
import uuid
import json
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel, HttpUrl
from app.models.chunk import Chunk

from app.services.processor.pdf_processor import PDFProcessor
from app.services.processor.document_chunker import DocumentChunker
from app.services.retrieval.retriever import Retriever
from app.services.crawler.web_ingestion_service import WebIngestionService


router = APIRouter()


UPLOAD_DIR = Path("data/uploads")
INDEX_DIR = "data/index"

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".txt",
    ".md",
    ".pptx",
    ".xlsx",
    ".csv",
}

MAX_FILE_SIZE = 25 * 1024 * 1024


# =========================================================
# URL REQUEST MODEL
# =========================================================

class URLIngestionRequest(BaseModel):
    url: HttpUrl


# =========================================================
# PDF / FILE UPLOAD
# =========================================================

@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...)
):

    # =====================================================
    # 1. VALIDATE FILE
    # =====================================================

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file was provided."
        )

    extension = Path(
        file.filename
    ).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file type. "
                "Supported formats: PDF, DOCX, TXT, MD, "
                "PPTX, XLSX and CSV."
            )
        )

    # -----------------------------------------------------
    # Current ingestion pipeline supports PDF processing.
    # -----------------------------------------------------

    if extension != ".pdf":
        raise HTTPException(
            status_code=400,
            detail=(
                "Document ingestion currently supports "
                "PDF files only."
            )
        )

    # =====================================================
    # 2. CREATE DOCUMENT ID
    # =====================================================

    document_id = uuid.uuid4().hex

    document_dir = (
        UPLOAD_DIR / document_id
    )

    document_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    file_path = (
        document_dir / file.filename
    )

    # =====================================================
    # 3. SAVE UPLOADED FILE
    # =====================================================

    total_size = 0

    try:

        with file_path.open("wb") as buffer:

            while True:

                data = await file.read(
                    1024 * 1024
                )

                if not data:
                    break

                total_size += len(data)

                if total_size > MAX_FILE_SIZE:

                    file_path.unlink(
                        missing_ok=True
                    )

                    raise HTTPException(
                        status_code=413,
                        detail=(
                            "File size cannot exceed 25 MB."
                        )
                    )

                buffer.write(data)

    except HTTPException:
        raise

    except Exception as exc:

        shutil.rmtree(
            document_dir,
            ignore_errors=True
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to save the uploaded document."
            )
        ) from exc

    # =====================================================
    # 4. PROCESS PDF
    # =====================================================

    try:

        pdf_processor = PDFProcessor()

        document = pdf_processor.process(
            str(file_path)
        )

    except Exception as exc:

        shutil.rmtree(
            document_dir,
            ignore_errors=True
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "The file was uploaded, but PDF "
                "processing failed."
            )
        ) from exc

    # =====================================================
    # 5. CREATE CHUNKS
    # =====================================================

    try:

        chunker = DocumentChunker()

        new_chunks = chunker.create_chunks(
            document
        )

    except Exception as exc:

        shutil.rmtree(
            document_dir,
            ignore_errors=True
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "The PDF was processed, but "
                "document chunking failed."
            )
        ) from exc

    if not new_chunks:

        shutil.rmtree(
            document_dir,
            ignore_errors=True
        )

        raise HTTPException(
            status_code=422,
            detail=(
                "No readable text could be extracted "
                "from the uploaded PDF."
            )
        )

    # =====================================================
    # 6. ASSIGN DOCUMENT ID + METADATA
    # =====================================================

    for chunk in new_chunks:

        chunk.document_id = document_id

        if chunk.metadata is None:
            chunk.metadata = {}

        chunk.metadata.update(
            {
                "source_type": "pdf",
                "source": str(file_path),
                "document_title": file_path.stem,
                "document_id": document_id,
                "filename": file.filename,
                "uploaded": True,
            }
        )

    # =====================================================
    # 7. LOAD EXISTING KNOWLEDGE BASE
    # =====================================================

    try:

        retriever = Retriever()

        retriever.load(
            INDEX_DIR
        )

        existing_chunks = list(
            retriever.chunks
        )

    except Exception as exc:

        print(
            "Existing knowledge base could not be loaded:",
            exc
        )

        existing_chunks = []

    # =====================================================
    # 8. GIVE NEW CHUNKS UNIQUE IDS
    # =====================================================

    start_id = len(
        existing_chunks
    )

    for index, chunk in enumerate(
        new_chunks
    ):

        chunk.id = (
            start_id + index
        )

    all_chunks = (
        existing_chunks +
        new_chunks
    )

    # =====================================================
    # 9. REBUILD FAISS INDEX
    # =====================================================

    try:

        retriever = Retriever()

        retriever.index(
            all_chunks
        )

        Path(INDEX_DIR).mkdir(
            parents=True,
            exist_ok=True
        )

        retriever.save(
            INDEX_DIR
        )

    except Exception as exc:

        shutil.rmtree(
            document_dir,
            ignore_errors=True
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "The document was processed, but "
                "indexing failed."
            )
        ) from exc

    # =====================================================
    # 10. VERIFY INDEX
    # =====================================================

    try:

        verification = Retriever()

        verification.load(
            INDEX_DIR
        )

        uploaded_chunks = [
            chunk
            for chunk in verification.chunks
            if str(
                chunk.document_id
            ) == str(document_id)
        ]

        if not uploaded_chunks:

            raise RuntimeError(
                "Uploaded document was not found "
                "in the saved knowledge base."
            )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "The document was uploaded, but "
                "knowledge-base verification failed."
            )
        ) from exc

    # =====================================================
    # 11. SUCCESS
    # =====================================================

    return {
        "document_id": document_id,
        "filename": file.filename,
        "file_type": extension.lstrip("."),
        "size_bytes": total_size,
        "chunks": len(uploaded_chunks),
        "total_indexed_chunks": len(
            verification.chunks
        ),
        "status": "indexed",
        "message": (
            f"{file.filename} uploaded and indexed "
            "successfully. You can now ask questions "
            "about the uploaded document."
        ),
    }


# =========================================================
# WEBSITE / URL INGESTION
# =========================================================

@router.post("/documents/ingest-url")
async def ingest_url(
    request: URLIngestionRequest
):
    """
    Crawl and index a website.
    """

    url = str(request.url)

    service = WebIngestionService(
    max_pages=1,
    max_depth=0,
)

    try:

        result = await service.ingest(
            url
        )

        if result.get("pages"):
         result["document_id"] = result["pages"][0]["document_id"]

        return {
            **result,
            "message": (
                "Website crawled and indexed successfully."
            ),
        }

    except ValueError as exc:

        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except Exception as exc:

         import traceback

         print("\n========== WEBSITE INGESTION ERROR ==========")
         print("Exception type:", type(exc).__name__)
         print("Exception repr:", repr(exc))
         traceback.print_exc()
         print("=============================================\n")

         raise HTTPException(
            status_code=500,
            detail=(
                f"Website ingestion failed: "
                f"{type(exc).__name__}: {repr(exc)}"
            )
         ) from exc


@router.get("/documents")
def list_documents():
    chunks_path = Path("data/index/chunks.json")

    if not chunks_path.exists():
        return []

    chunks_data = json.loads(
        chunks_path.read_text(encoding="utf-8")
    )

    documents = {}

    for chunk in chunks_data:
        document_id = str(chunk.get("document_id", ""))
        if not document_id:
            continue

        metadata = chunk.get("metadata") or {}

        source_id = metadata.get("source_id")

        # A PDF may not have a source_id.
        # In that case, treat the document itself as the source.
        source_key = source_id or document_id

        if document_id not in documents:
            documents[document_id] = {
                "document_id": document_id,
                "source_id": source_id,
                "title": metadata.get(
                    "document_title",
                    chunk.get("heading", "Untitled document")
                ),
                "url": metadata.get(
                    "source_url",
                    metadata.get("source", "")
                ),
                "source_type": metadata.get(
                    "source_type",
                    "unknown"
                ),
                "chunks": 0,
            }

        documents[document_id]["chunks"] += 1

    # Deduplicate repeated ingestions of the same URL.
    # Keep the most recently indexed document.
    unique_documents = {}

    for document in documents.values():
        url = str(document.get("url", "")).rstrip("/")

        if url.startswith("http://"):
            url = "https://" + url[len("http://"):]

        if document["source_type"] in {"website", "html"} and url:
            key = url
        else:
            key = document["document_id"]

        unique_documents[key] = document

    return list(unique_documents.values())

@router.delete("/documents")
def delete_document(document_id: str):
    chunks_path = Path(INDEX_DIR) / "chunks.json"

    if not chunks_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Knowledge base not found."
        )

    # ---------------------------------------------
    # Load current chunks
    # ---------------------------------------------

    chunks_data = json.loads(
        chunks_path.read_text(
            encoding="utf-8"
        )
    )

    document_id = str(document_id)

    matching_chunks = [
        chunk
        for chunk in chunks_data
        if str(chunk.get("document_id", "")) == document_id
    ]

    if not matching_chunks:
        raise HTTPException(
            status_code=404,
            detail="Document not found in knowledge base."
        )

    # ---------------------------------------------
    # Remove the document's chunks
    # ---------------------------------------------

    remaining_chunks = [
        chunk
        for chunk in chunks_data
        if str(chunk.get("document_id", "")) != document_id
    ]

    # ---------------------------------------------
    # Rebuild FAISS index
    # ---------------------------------------------

    if remaining_chunks:
        retriever = Retriever()

        retriever.index([
         Chunk(**chunk)
         for chunk in remaining_chunks
       ])

        retriever.save(INDEX_DIR)

    else:
        # Do not allow the knowledge base to become
        # unusable when the last document is deleted.
        raise HTTPException(
            status_code=400,
            detail="Cannot delete the last document in the knowledge base."
        )

    # ---------------------------------------------
    # Remove uploaded PDF from disk if applicable
    # ---------------------------------------------

    source_type = (
        matching_chunks[0]
        .get("metadata", {})
        .get("source_type", "")
    )

    if source_type == "pdf":
        source = (
            matching_chunks[0]
            .get("metadata", {})
            .get("source", "")
        )

        if source:
            pdf_path = Path(source)

            try:
                if pdf_path.exists():
                    pdf_path.unlink()

                # Remove the UUID upload directory if empty.
                if pdf_path.parent.exists():
                    try:
                        pdf_path.parent.rmdir()
                    except OSError:
                        pass

            except Exception as exc:
                print(
                    "Warning: could not remove uploaded file:",
                    exc
                )

    return {
        "status": "deleted",
        "document_id": document_id,
        "deleted_chunks": len(matching_chunks),
        "remaining_chunks": len(remaining_chunks),
        "message": "Document removed from the knowledge base."
    }