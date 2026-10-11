from typing import Any, Dict

from pydantic import BaseModel, Field


class Chunk(BaseModel):
    id: int
    document_id: str
    heading: str
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)