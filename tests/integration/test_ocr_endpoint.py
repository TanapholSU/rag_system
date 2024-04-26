import os
import time

from fastapi.testclient import TestClient
from fastapi import status
from main import app
from config import app_config
from api.schemas.ocr import OcrResponse
from api.service.storage.minio_storage import MinioStorage
from vector_db_task import import_doc_to_vector_store


client = TestClient(app)

m = MinioStorage(
    endpoint=app_config.storage_service_endpoint,
    bucket_name=app_config.storage_bucket_name,
    access_key=app_config.storage_access_key,
    secret_key=app_config.storage_secret_key,
    secure=app_config.storage_secure_connection,
)


def test_ocr_endpoint_with_valid_sample_data():
    """
    Testing ocr endpoint when providing valid sample pdf file.
    Initially, the http status response from this endpoint should be 202 ACCEPT.
    Also, the response payload should be OcrResponse

    After the task is finished, the result should be success.
    """
    # upload files first
    signed_url = m.upload(
        "建築基準法施行令.pdf",
        open(os.path.join("test_files", "sample", "建築基準法施行令.pdf"), "rb"),
    )

    response = client.post(url="/v1/ocr", json={"signed_url": signed_url})

    assert response.status_code == status.HTTP_202_ACCEPTED
    result = response.json()
    response = OcrResponse(**result)

    task_id = response.task_id

    while True:
        time.sleep(5)
        result = import_doc_to_vector_store.AsyncResult(task_id)
        if result.status == "SUCCESS":
            break

    # also check the get status endpoint here
    response = client.get(url=f"/v1/ocr/{task_id}")

    result = response.json()
    response = OcrResponse(**result)

    assert response.task_status == "SUCCESS"


def test_ocr_endpoint_with_invalid_data():
    """
    Testing ocr endpoint when providing non-existing file.
    Initially, the http status response from this endpoint should be 202 ACCEPT.
    Also, the response payload should be OcrResponse with task id

    After the task is processed, the result should become FAILURE with some error message
    """
    # upload files first

    response = client.post(
        url="/v1/ocr", json={"signed_url": "http://localhost/test_invalid_file.jpg"}
    )

    assert response.status_code == status.HTTP_202_ACCEPTED
    result = response.json()
    response = OcrResponse(**result)

    task_id = response.task_id

    while True:
        time.sleep(5)
        result = import_doc_to_vector_store.AsyncResult(task_id)
        if result.status == "FAILURE":
            break

    # also check the get status endpoint here
    response = client.get(url=f"/v1/ocr/{task_id}")

    result = response.json()
    response = OcrResponse(**result)
    assert response.task_status == "FAILURE"
    assert response.detail == "Could not find target file"
