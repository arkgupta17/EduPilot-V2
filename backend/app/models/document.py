from pydantic import BaseModel
from typing import Dict, Any


class Document(BaseModel):
    id: str
    title: str
    source_type: str
    url: str
    content: str
    metadata: Dict[str, Any]