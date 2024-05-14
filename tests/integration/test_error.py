import openai
import pytest
import os
import qdrant_client

from fastapi.testclient import TestClient
from fastapi import status
from celery.exceptions import CeleryError
import qdrant_client.http
import qdrant_client.http.exceptions

from main import app
from config import app_config
from vector_db_task import import_doc_to_vector_store
from api.service.storage.minio_storage import MinioStorage
from api.common.error import (
    LlmOpenAiAPIConnectionError,
    LlmOpenAiAPIConnectionError,
    LlmOpenAiServiceError,
    LlmOpenAiAuthenticationError,
    LlmOpenAiBadRequestError,
    LlmOpenAiPermissionError,
    LlmOpenAiRateLimitError,
    LlmError,
    LlmVectorStoreError,
    ObjectStorageError,
)

object_storage = MinioStorage(
    endpoint=app_config.storage_service_endpoint,
    bucket_name=app_config.storage_bucket_name,
    access_key=app_config.storage_access_key,
    secret_key=app_config.storage_secret_key,
)

test_file_signed_url = object_storage.upload(
    "test_file", open(os.path.join("test_files", "tektome.jpg"), "rb")
)


@pytest.fixture(scope="module")
def signed_url():
    return test_file_signed_url


def test_upload_with_object_storage_error(mocker):
    """
    Test upload endpoint when the called MinioStorage.upload() function is patched to raise ObjectStorageError.
    The returned response from API should be correct json with HTTP status 500
    """

    # patch function called in query() to trigger error handling code
    mocker.patch(
        "api.service.storage.minio_storage.MinioStorage.upload",
        side_effect=ObjectStorageError("some error"),
    )

    client = TestClient(app)

    files = [
        (
            "files",
            open(os.path.join("test_files", "sample", "建築基準法施行令.pdf"), "rb"),
        )
    ]
    response = client.post(url="/v1/upload", files=files)

    output = response.json()
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert output["error_code"] == "ObjectStorageError"
    assert output["detail"] == "some error"


def test_upload_with_unexpected_error(mocker):
    """
    Test upload endpoint when the called MinioStorage.upload() function is patched.
    So, API should handle an error we don't specifically handle.
    The returned error code should be APIerror with HTTP status 500.
    """

    # patch function called in query() to trigger error handling code
    mocker.patch(
        "api.service.storage.minio_storage.MinioStorage.upload",
        side_effect=ValueError("value error"),
    )

    client = TestClient(app)

    files = [
        (
            "files",
            open(os.path.join("test_files", "sample", "建築基準法施行令.pdf"), "rb"),
        )
    ]
    response = client.post(url="/v1/upload", files=files)

    output = response.json()
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert output["error_code"] == "APIError"
    assert output["detail"] == "Unknown error"


def test_mock_ocr_with_unexpected_error(mocker):
    """
    Test OCR endpoint when the called import_doc_to_vector_store.delay function is patched.
    Thus, the endpoint should catch the error we don't specifically handle.
    The API should wrap the raised error to APIerror and returns it as json with with HTTP status 500.
    """

    # patch function called in query() to trigger error handling code
    mocker.patch(
        "vector_db_task.import_doc_to_vector_store.delay",
        side_effect=ValueError("value error"),
    )

    client = TestClient(app)

    response = client.post(
        url="/v1/ocr", json={"signed_url": "http://localhost/建築基準法施行令.pdf"}
    )

    output = response.json()
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert output["error_code"] == "APIError"
    assert output["detail"] == "Unknown error"


def test_mock_ocr_with_celery_error(mocker):
    """
    Test OCR endpoint when the called import_doc_to_vector_store.delay function is patched to raise Celery error.
    The API should wrap the error to APIerror and returns it as json with with HTTP status 500.
    """

    # patch function called in query() to trigger error handling code
    mocker.patch(
        "vector_db_task.import_doc_to_vector_store.delay", side_effect=CeleryError()
    )

    client = TestClient(app)

    response = client.post(
        url="/v1/ocr", json={"signed_url": "http://localhost/建築基準法施行令.pdf"}
    )

    output = response.json()
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert output["error_code"] == "APIError"
    assert output["detail"] == "There is problem with backend side (celery)"


def test_get_ocr_status_with_celery_error(mocker):
    """
    Test OCR status endpoint.
    The called import_doc_to_vector_store.AsyncResult() is patched to raise Celery error.
    The API should wrap the error to APIerror and returns it as json with with HTTP status 500.
    """

    # patch function called in query() to trigger error handling code
    mocker.patch(
        "vector_db_task.import_doc_to_vector_store.AsyncResult",
        side_effect=CeleryError(),
    )

    client = TestClient(app)

    response = client.get(url="/v1/ocr/123545")

    output = response.json()
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert output["error_code"] == "APIError"
    assert output["detail"] == "There is problem with backend side (celery)"


def test_get_ocr_status_with_unexpected_error(mocker):
    """
    Test OCR status endpoint.
    The called import_doc_to_vector_store.AsyncResult() is patched to raise an unexpected error.
    The API should wrap the error to APIerror and returns it as json with with HTTP status 500.
    """

    # patch function called in query() to trigger error handling code
    mocker.patch(
        "vector_db_task.import_doc_to_vector_store.AsyncResult",
        side_effect=ValueError("value error"),
    )

    client = TestClient(app)

    response = client.get(url="/v1/ocr/123545")

    output = response.json()
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert output["error_code"] == "APIError"
    assert output["detail"] == "Unknown error"


def test_extract_with_llm_error(mocker, signed_url):
    """
    Test LLM endpoint with OpenAI, LangChain, and unexpected errors.
    The function used in LLM service is patched to raise those errors.
    The API should wrap the error to appropriate custom error and returns it as json with with HTTP status 500.
    """

    side_effects = [
        openai.APITimeoutError(request=mocker.MagicMock()),
        openai.APIConnectionError(request=mocker.MagicMock()),
        openai.APIError(
            message="Test error", request=mocker.MagicMock(), body=mocker.MagicMock()
        ),
        openai.AuthenticationError(
            message="Can't authenticate",
            response=mocker.MagicMock(),
            body=mocker.MagicMock(),
        ),
        openai.BadRequestError(
            message="Bad user", response=mocker.MagicMock(), body=mocker.MagicMock()
        ),
        openai.PermissionDeniedError(
            message="No permission",
            response=mocker.MagicMock(),
            body=mocker.MagicMock(),
        ),
        openai.RateLimitError(
            message="too many requests!",
            response=mocker.MagicMock(),
            body=mocker.MagicMock(),
        ),
        openai.OpenAIError(),
        qdrant_client.http.exceptions.ApiException(),
    ]

    exepected_error_codes = [
        LlmOpenAiAPIConnectionError,
        LlmOpenAiAPIConnectionError,
        LlmOpenAiServiceError,
        LlmOpenAiAuthenticationError,
        LlmOpenAiBadRequestError,
        LlmOpenAiPermissionError,
        LlmOpenAiRateLimitError,
        LlmError,
        LlmVectorStoreError,
    ]

    # patch function called in Gpt35LLMService.query() to trigger error handling code
    mocker.patch(
        "api.service.llm.gpt35.Gpt35LLMService._get_retriever", side_effect=side_effects
    )

    for error in exepected_error_codes:
        client = TestClient(app)
        response = client.post(
            "/v1/extract", json={"query": "hello", "signed_url": signed_url}
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        output = response.json()
        assert output["error_code"] == error.__name__
