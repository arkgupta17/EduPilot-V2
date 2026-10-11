from fastapi import APIRouter

from app.models.chat import ChatRequest, ChatResponse
from app.services.rag_pipeline import RAGPipeline


router = APIRouter()

rag_pipeline = RAGPipeline()


@router.post(
    "/chat",
    response_model=ChatResponse
)
def chat(request: ChatRequest):


    return rag_pipeline.answer(
        request.query,
        request.history,
        document_id=request.document_id,
        source_id=request.source_id

    )