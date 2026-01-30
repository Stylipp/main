from pydantic import BaseModel, HttpUrl


class UploadResponse(BaseModel):
    """Response returned after a successful file upload."""

    url: HttpUrl
    key: str
    size: int
