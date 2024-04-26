from pydantic import BaseModel


class OcrResponse(BaseModel):
    """
    Response payload for ocr endpoint. For more information, please refer to README.
    """

    task_id: str
    task_status: str
    detail: str | None


class OcrRequest(BaseModel):
    """
    Request payload for ocr endpoint. For more information, please refer to README.
    """

    signed_url: str
