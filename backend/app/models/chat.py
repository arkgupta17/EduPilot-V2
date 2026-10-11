from pydantic import BaseModel
from pydantic import Field


class ChatRequest(BaseModel):
    query: str
    history: list[dict] = Field(default_factory=list)
    document_id: str | None = None
    source_id: str | None = None


class Source(BaseModel):
    heading: str
    url: str
    score: float


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]