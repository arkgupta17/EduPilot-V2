from pydantic import BaseModel


class RawPage(BaseModel):
    url: str
    html: str