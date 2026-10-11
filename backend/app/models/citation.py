from pydantic import BaseModel


class Citation(BaseModel):
    title: str
    url: str
    page: str