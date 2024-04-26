from pydantic import BaseModel


class ExtractRequest(BaseModel):
    """
    Request payload for extract endpoint. For more information, please refer to README.
    """

    query: str
    signed_url: str


class ExtractResponse(BaseModel):
    """
    Response payload for extract endpoint. For more information, please refer to README.
    """

    query: str
    signed_url: str
    filename: str
    response: str
