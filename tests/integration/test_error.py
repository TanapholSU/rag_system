from fastapi.testclient import TestClient
from fastapi import status
import qdrant_client.http
import qdrant_client.http.exceptions
from main import app
from config import app_config
from api.service.storage.minio_storage import MinioStorage
import openai
import pytest
import os
import qdrant_client
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


def test_llm_error(mocker, signed_url):
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

    # patch function called in query() to trigger error handling code
    mocker.patch(
        "api.service.llm.gpt35.Gpt35LLMService._retrieve_docs", side_effect=side_effects
    )

    for error in exepected_error_codes:
        client = TestClient(app)
        response = client.post(
            "/v1/extract", json={"query": "hello", "signed_url": signed_url}
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        output = response.json()
        assert output["error_code"] == error.__name__
