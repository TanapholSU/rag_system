from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, NonNegativeInt


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # OpenAI API KEY
    openai_api_key: str = Field("")

    # Vector database URL
    llm_vector_db_url: str = Field(default="http://localhost:6333")

    # Vector database collection name
    llm_vector_db_collection_name: str = Field(default="tektome")

    # During LLM process, the large document is splitted for vector embedding and query process.
    # This parameter specifies the chunk size of the splitted text
    llm_preprocess_chunk_size: NonNegativeInt = Field(default=128)

    # Specified the chunk overlap parameter during document splitting
    llm_preprocess_chunk_overlap: NonNegativeInt = Field(default=20)

    # Maximum mumber of relevant documents to be retrieved from vector db
    llm_vector_search_top_k: NonNegativeInt = Field(default=1)

    # Service endpoint of object storage. No need to include http://
    storage_service_endpoint: str = Field(default="localhost:9000")

    # access key for the object storage
    storage_access_key: str = Field(default="tektome")

    # secret key for accessing the object storage
    storage_secret_key: str = Field(default="tektomeSecret")

    # target bucket name
    storage_bucket_name: str = Field(default="tektome")

    # type of connection to object storage
    storage_secure_connection: bool = Field(default=False)

    # Celery is used to process long running ocr task.
    # This parameter is for celery broker url (message communication)
    celery_broker_url: str = Field(default="redis://localhost:6379/0")

    # Celery result backend url (for storing result and state of the task)
    celery_result_backend_url: str = Field(default="redis://localhost:6379/0")

    # debug mode (will include traceback in the response)
    debug: bool = Field(default=False)


app_config = AppSettings()
