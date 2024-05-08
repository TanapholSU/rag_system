import logging
from fastapi.concurrency import run_in_threadpool
from fastapi import APIRouter, UploadFile, status
from fastapi.responses import JSONResponse, Response
from celery.exceptions import CeleryError
from vector_db_task import import_doc_to_vector_store

from api.service.storage.minio_storage import MinioStorage
from api.service.llm.gpt35 import Gpt35LLMService
from api.common.utils import is_allowed_content_type, get_filename_from_signed_url
from api.schemas.upload import UploadResponse, UploadListResponse
from api.common.error import (
    ObjectStorageError,
    UnsupportedFileTypeError,
    ObjectStorageFileNotFoundError,
    LlmError,
    APIError,
)
from api.schemas.ocr import OcrRequest, OcrResponse
from api.schemas.extract import ExtractRequest, ExtractResponse
from config import app_config

logger = logging.getLogger(__name__)
router = APIRouter()

llm_service = Gpt35LLMService(
    openai_api_key=app_config.openai_api_key,
    vector_db_url=app_config.llm_vector_db_url,
    vector_db_collection_name=app_config.llm_vector_db_collection_name,
    text_split_chunk_size=app_config.llm_preprocess_chunk_size,
    text_split_chunk_overlap=app_config.llm_preprocess_chunk_overlap,
    vector_search_top_k=app_config.llm_vector_search_top_k,
)


object_storage_service = MinioStorage(
    endpoint=app_config.storage_service_endpoint,
    bucket_name=app_config.storage_bucket_name,
    access_key=app_config.storage_access_key,
    secret_key=app_config.storage_secret_key,
)


@router.post("/upload")
async def upload(files: list[UploadFile]) -> UploadListResponse:
    """
    Upload endpoint for rag system. The uploaded files are stored in the object storage service
    For more information, please refer to README

    Args:
        - list of UploadFile objects

    Returns:
        - UploadResultResponse

    Raises:
        - UnsupportedFileTypeError if any file type of the uploaded file is not among supported types
        - ObjectStorageError if there is problem with object storage service
    """

    logger.info(f"Got file upload request: {len(files)} files")

    # perform file format check from mime type (limited to pdf, tiff, png,jpeg formats).
    not_allowed_files = []
    for file in files:
        if not is_allowed_content_type(file.content_type):
            not_allowed_files.append(file.filename)

    if len(not_allowed_files) > 0:
        not_allowed_files_str = ", ".join(not_allowed_files)
        logger.error(
            f"The request contains unsupported file type > {not_allowed_files_str}"
        )
        raise UnsupportedFileTypeError(not_allowed_files_str)

    # start uploading operations
    upload_results = []
    try:
        for file in files:
            file_id = await run_in_threadpool(
                object_storage_service.upload, file.filename, file.file, file.size
            )
            # file_id = object_storage_service.upload(file.filename, file.file, file.size)
            result = UploadResponse(filename=file.filename, signed_url=file_id)
            upload_results.append(result)

        logger.info(f"All files are uploaded")
    except ObjectStorageError as err:
        logger.exception("There is a problem with object storage while uploading")
        raise
    except Exception as err:
        raise APIError("Unknown error") from err

    return UploadListResponse(upload_results=upload_results)


@router.post("/ocr")
async def mock_ocr(request: OcrRequest, response: Response) -> OcrResponse:
    """
    This is mock ocr endpoint. As described in the requirements, this function does:
     - simulate the OCR service by getting json results associated with the input file
     - process json result through open ai embedding and import to vector store

    Because processing might take long time to finish. In this project, the celery is used for processing the json result and importing task
    For more information, please refer to README

    Args:
        - OcrRequest which contains signed URL of the file to be processed

    Returns:
        - OcrResponse which contains task id (of celery) and the current task status. Client can check the task status using GET method to /ocr/<task_id> endpoint

    Raises:
        - ObjectStorageFileNotFoundError if requested file is not sample file
        - APIError if there is problem with the backend (celery)

    """

    try:
        url = request.signed_url
        logger.info(f"Got OCR request for url: {url}")

        original_filename = get_filename_from_signed_url(url)

        if (
            "建築基準法施行令" not in original_filename
            and "東京都建築安全条例" not in original_filename
        ):
            logger.error(f"The requested file: {original_filename} is not sample file")
            raise ObjectStorageFileNotFoundError

        result = import_doc_to_vector_store.delay(url)
        response.status_code = status.HTTP_202_ACCEPTED
        return OcrResponse(
            task_id=result.id, task_status=result.status, detail=str(result.result)
        )

    except CeleryError as err:
        logger.exception("Found eror related to celery while processing ocr request")
        raise APIError("There is problem with backend side (celery)") from err

    except ObjectStorageFileNotFoundError as err:
        logger.exception("The requested file is not sample files!")
        raise

    except Exception as err:
        raise APIError("Unknown error") from err


@router.get("/ocr/{task_id}")
async def get_ocr_status(task_id: str) -> OcrResponse:
    """
    This endpoint is used for checking the status of mocked ocr operations

    Args:
        - task_id:  id of the submitted task

    Returns:
        - Current task status (OcrResponse)
    """
    try:
        logger.info(f"Check ocr status for task: {task_id}")
        result = import_doc_to_vector_store.AsyncResult(task_id)
        return OcrResponse(
            task_id=result.id, task_status=result.status, detail=str(result.result)
        )
    except CeleryError as err:
        logger.exception("Found eror related to celery while checking task status")
        raise APIError("There is problem with backend side (celery)") from err
    except Exception as err:
        raise APIError("Unknown error") from err


@router.post("/extract")
async def extract(request: ExtractRequest) -> ExtractResponse:
    """
    Extract endpoint for RAG. For more information, please refer to README

    Args:
        - query: query text
        - signed_url:  the document to be used as context

    Returns:
        - ExtractResponse

    Raises:
        - ObjectStorageFileNotFoundError if file does not exist
        - LlmError if there is problem with llm service
        - ApiError for unexepected error
    """

    query = request.query
    signed_url = request.signed_url

    try:
        filename = get_filename_from_signed_url(signed_url)
        logger.info(f"Got extract request for file {filename}")

        if not object_storage_service.contains_file(filename):
            raise ObjectStorageFileNotFoundError

        result = await run_in_threadpool(llm_service.query, query, signed_url)
        # result = llm_service.query(query, signed_url)

        return ExtractResponse(
            query=query, signed_url=signed_url, filename=filename, response=result
        )
    except ObjectStorageFileNotFoundError as err:
        logger.error(
            f"Abort extract operation as file {filename} does not exist on the object storage. "
        )
        raise err

    except LlmError as err:
        logger.exception(f"Abort extract operation due to problem with LLM backend")
        raise err

    except Exception as err:
        logger.exception(f"Abort extract operation due to unexpected problem")
        raise APIError from err


@router.get("/health")
async def health_check() -> JSONResponse:
    """
    The dummy healthcheck endpoint
    """
    return {"status": "API itself is ok !"}
