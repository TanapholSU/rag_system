import os

from fastapi.testclient import TestClient
from fastapi import status
from main import app
from api.service.llm import load_ocr_json_result
from api.routers.tektome import llm_service, object_storage_service
from api.schemas.extract import ExtractResponse


def test_extract_endpoint_with_invalid_file():
    """
    Testing endpoint when the non-existing file.
    We should get 400 bad request error
    """
    client = TestClient(app)
    response = client.post(
        "/v1/extract", json={"query": "hello", "signed_url": "file_not_found"}
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST

    response_data = response.json()
    assert (
        response_data["error_code"] == "ObjectStorageFileNotFoundError"
    ), "Found unexpected error code"
    assert (
        response_data["detail"] == "Could not find target file"
    ), "Unexpected error detail"


def test_extract_endpoint_with_valid_file():
    """
    Test the extract endpoint with the existing file.
    First we upload the file + import json data to the object storage and vector database.
    Then, we query and check whether extract endpoint return proper result or not.
    However, I'm not sure how to check the relatedness of the response from chat complete in llm.
    """

    # upload the file first
    with open(
        os.path.join("test_files", "sample", "東京都建築安全条例.pdf"), "rb"
    ) as fp:
        signed_url = object_storage_service.upload(
            "東京都建築安全条例.pdf", file_data=fp, append_uuid_to_filename=False
        )

    # import json document
    docs = load_ocr_json_result(
        os.path.join("test_files", "ocr", "東京都建築安全条例.json"),
        source_name="東京都建築安全条例.pdf",
    )

    llm_service.import_docs_to_vector_store(docs)

    # send request with query and target file
    query = "When Tokyo Building Safety Regulation is made"

    client = TestClient(app)
    response = client.post(
        "/v1/extract", json={"query": query, "signed_url": signed_url}
    )

    assert response.status_code == status.HTTP_200_OK
    extract_response = ExtractResponse(**response.json())

    assert (
        extract_response.query == query
    ), "The query field in response is different from the request"
    assert (
        extract_response.signed_url == signed_url
    ), "The signed url in response is different from the request"
    assert (
        extract_response.filename == "東京都建築安全条例.pdf"
    ), "The filename in the response is different from the request"

    # TODO: find better way to check the relevancy of the output because output is non-deterministic
    # assert "December" in extract_response.response
    # assert "1950" in extract_response.response
