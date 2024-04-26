import logging
import os
from celery import Celery
from api.service.llm import load_ocr_json_result
from api.common.error import ObjectStorageFileNotFoundError
from api.service.llm.gpt35 import Gpt35LLMService
from api.service.storage.minio_storage import MinioStorage
from api.common.utils import get_filename_from_signed_url
from config import app_config

logger = logging.getLogger(__name__)


app = Celery("vector_db_task", broker=app_config.celery_broker_url)
app.conf.result_backend = app_config.celery_result_backend_url
app.conf.update(result_extended=True)

llm = Gpt35LLMService(
    openai_api_key=app_config.openai_api_key,
    vector_db_url=app_config.llm_vector_db_url,
    vector_db_collection_name=app_config.llm_vector_db_collection_name,
    text_split_chunk_size=app_config.llm_preprocess_chunk_size,
    text_split_chunk_overlap=app_config.llm_preprocess_chunk_overlap,
    vector_search_top_k=app_config.llm_vector_search_top_k,
)

object_storage = MinioStorage(
    endpoint=app_config.storage_service_endpoint,
    bucket_name=app_config.storage_bucket_name,
    access_key=app_config.storage_access_key,
    secret_key=app_config.storage_secret_key,
)


@app.task
def import_doc_to_vector_store(target_file_signed_url: str):
    """
    The celery task to import the mocked ocr result associated with the target file.

    Args:
        - target_file_signed_url : the signed url of the target file

    Raises:
        - ObjectStorageFileNotFoundError if the input file is not sample
        - LLMError family if there is problem with llm service
        - APIError for unexpected error

    """

    filename = get_filename_from_signed_url(target_file_signed_url)
    logger.debug(f"Requested file: {filename}")
    if "建築基準法施行令.pdf" in filename:
        docs = load_ocr_json_result(
            os.path.join("test_files", "ocr", "建築基準法施行令.json"),
            source_name=target_file_signed_url,
        )

    elif "東京都建築安全条例.pdf" in filename:
        docs = load_ocr_json_result(
            os.path.join("test_files", "ocr", "東京都建築安全条例.json"),
            source_name=target_file_signed_url,
        )
    else:
        logger.error(f"The requested file: {filename} is not sample file")
        raise ObjectStorageFileNotFoundError

    llm.import_docs_to_vector_store(docs)
    logger.info("Finished importing document to vector db")


if __name__ == "__main__":
    worker = app.Worker()
    worker.start()
