from pydantic import BaseModel
from typing import List


class UploadResponse(BaseModel):
    """
    Response payload for upload endpoint. For more information, please refer to README.
    """

    filename: str
    signed_url: str | None


class UploadListResponse(BaseModel):
    """
    Request payload for upload endpoint. For more information, please refer to README.
    """

    upload_results: List[UploadResponse]
