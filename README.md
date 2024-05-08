
# General structure of the project

- api:  the RAG services with endpoints
    - common : utility and error module
    - routers : router for the RAG service
    - schema : Json schema for input/output of each endpoint
    - service:  contains wrapper of external   LLM service and Object storage services

- vector_db_task.py :  celery worker to process import data to vector database (received from OCR endpoint)
- config.py : stores configuration loaded from env
- main.py : fastapi app 
- tests: integration and unit tests

# Notes:

- For LLM and object storage wrapper, the abstract base classes are implemented as an outline for each service. In the future, if we want to introduce new object storage service like Azure Blog storage. We can inherit the base class to make sure that it contains the same set of functions/method we need.

- All Minio storage and Qdrant Vector database are deployed as docker containers. 

- Qdrant vector database is used instead of pinecone because we can host it locally. It also supports in-memory mode which is useful for some testing

- Mainly, most of the tests are integration tests and only public functions are tests due to the time constrant.

- In actual git practice, it is not recommended to store binary or large files to the git as it will make git very slow to pull. However, we store testing files in this repository for simplicity.

- Due to time constraints (having issues in the current company), error handling code are not fully tested.

- Signed URL expiration date is fixed to 7 days. It can be changeable as config parameter in the future if need

# Config file

All configuration related to the API should be defined in ENVIRONMENT or `.env` file

```
# OpenAI API KEY
OPENAI_API_KEY=<openai api key>

# Vector database url
LLM_VECTOR_DB_URL=http://qdrant:6333

# Vector database collection name
LLM_VECTOR_DB_COLLECTION_NAME=tektome

# During LLM process, the large document is splitted for vector embedding and query process.
# This parameter specifies the chunk size of the splitted text
LLM_PREPROCESS_CHUNK_SIZE=128

# Specified the chunk overlap parameter during document splitting
LLM_PREPROCESS_CHUNK_OVERLAP=20

# Maximum mumber of relevant documents to be retrieved from vector db
LLM_VECTOR_SEARCH_TOP_K=1

# Service endpoint of object storage. No need to include http://
STORAGE_SERVICE_ENDPOINT=minio:9000

# access key for the object storage
STORAGE_ACCESS_KEY=tektome

# secret key for accessing the object storage
STORAGE_SECRET_KEY=tektomeSecret

# target bucket name
STORAGE_BUCKET_NAME=tektome

# type of connection to object storage
STORAGE_SECURE_CONNECTION=False

# Celery is used to process long running ocr task.
# This parameter is for celery broker url (message communication)
CELERY_BROKER_URL=redis://redis:6379/0

# Celery result backend url (for storing result and state of the task)
CELERY_RESULT_BACKEND_URL=redis://redis:6379/0

# DEBUG mode. Default value is  False. If it's True, it outputs stacktrace in every error response obtained from API 
DEBUG=False
```


# Test & Deployment (locally)

Normally, if you want to run the test or deploy everything locally. Please follow these steps:

1. Rename `.env.default` to `.env` and just configure `OPENAI_API_KEY` parameter. 
Other parameters is configured for running locally so you don't need configure those.

2. To run the test locally, simply run `docker compose -f docker-compose-local.yml run --build tektome-test`. 
3. To deploy the rag system locally, please run run `docker compose -f docker-compose-local.yml down` to clean up the containers and then run `docker compose -f docker-compose-prod.yml up --build`.

In case that you want to use external service like S3 or external Qdrant database, 
please refer to comments in `.env` file and configure those related parameter accordingly. 

# Github Action 

After testing and building the docker image, the image should be pushed to `ghcr.io/tanapholsu/tektome_rag` 

# Endpoints

3 + 1 endpoints are implemented for RAG system:

## 1. /v1/upload (method: POST)

Here are requirements:

- Accept multiple files upload request in the following format : pdf, jpg, tiff, and png
- Save the file in object storage
- return list of file ids or signed URLs. 
- No security requirements
- There is no requirement on file size. So for simplicity, FastAPI UploadFile is used to handle the multipart-upload
- No details on what to do when a duplicated file is uploaded to the system

To achieve minimum requirements for this endpoint, local Minio docker is used and user is expected to used multi-part file upload method. 

When user upload to the endpoint,  we send the file stream of each UploadFile object to storage service for uploading. The result obtained from the object storage service is the signed URL for HEAD request. This is because the following reasons:

1. There is no requirement that user will later download the file later. 
2. For our OCR endpoint, there is no need to download the whole file because the preprocessed OCR result is used
3. For simplicity of the system (for current requirements). If we use unique file id, then we may have to use database to record the mapping between file id and the actual object name in the object storage

To handle file duplication, for now, the object storage service prepends UUID to file name before storing to the object storage.

If file is too large, UploadFile method may not be suitable choice as there is overhead when FASTAPI process the UploadFile.  Other option is to generated pre-signed URLs for POST requests and let the users directly upload the file using those URLs.  In this case, it should be faster but it will make user/frontend more complicate. Also, we cannot check the file type at this endpoint.

### Request payload
Please send the request using multipart/form upload

### Json Response payload

You should get the UploadListResponse object with HTTP status 200.
The UploadListResponse includes list of UploadResponse objects each of which contains signed-URL of the uploaded file.

#### UploadListResponse

| Attribute   | Type                   | Description                                                                          |
|-------------|------------------------|--------------------------------------------------------------------------------------|
| upload_results    | list                 | list of UploadResponse objects 

#### UploadResponse

| Attribute   | Type                   | Description                                                                          |
|-------------|------------------------|--------------------------------------------------------------------------------------|
| filename    | str                 | name of the uploaded file
| signed_url    | str                 | signed URL to the uploaded file 


---

## /v1/ocr (method: POST)

Here are requirements for this endpoint:
1. Simulate running OCR service. Only two sample files are used for testing. So, we just have to grab the associated json file and use it to import to vector store
2. OpenAI Embedding is applied on the content in the json file and store them in the vector database

- In our case, the input is signed URL from the upload endpoint 
- Field analyzeResult.content are extracted from json for further processing
- The extracted content is splinted to chunks and the vector embedding is applied to it before storing them in the vector database
- Because the processing time (reading json, embedding, and importing to vector database) may take very long time. It is not good for user to keep waiting.  Thus, we use celery to process such long running task.
- When the request comes, the file request is passed to the celery queue which will be processed later by celery backend worker. At the time of submission, user will immediately get the task information including task id.  They can check the status of that task id with another endpoint.

### Json Request payload

The request payload is OcrRequest object

| Attribute   | Type                   | Description                                                                          |
|-------------|------------------------|--------------------------------------------------------------------------------------|
| signed_url    | str                 | signed url of the target file to be imported to vector store

### Json Response payload

If the request file is sample files you should get the OcrResponse object with HTTP status 202.
Otherwise, you would get  ObjectStorageFileNotFoundError error with Http statuc 400 

#### OcrResponse

| Attribute   | Type                   | Description                                                                          |
|-------------|------------------------|--------------------------------------------------------------------------------------|
| task_id    | str                 | task id of the submitted job
| task_status | str                 | status of task (e.g., SUCCESS, FAILURE, PENDING)
| detail    | str or None              | error detail if there is

---

## /v1/ocr/<task_id> (method: GET)

This additional endpoint allows user to query the OCR task status from the task id obtained from UploadResponse object.

The json response is also OcrResponse object with HTTP status 200

---

## /v1/extract (method: POST)

Requirements are:
- input is query text and signed URL as input
- perform vector search using query text on the document in vector stored extracted from the file with signed_url
- use chat completion (chatprompt) to generate the answer 

### Json Request payload

The request payload is ExtractRequest object

| Attribute   | Type                   | Description                                                                          |
|-------------|------------------------|--------------------------------------------------------------------------------------|
| query       | str                 |  query 
| signed_url  | str                 | signed url of the target file

### Json response payload

You should get the ExtractResponse object with HTTP status 200.

| Attribute   | Type                   | Description                                                                          |
|-------------|------------------------|--------------------------------------------------------------------------------------|
| query       | str                 |  query 
| signed_url  | str                 | signed url of the target file
| response    | str                 | chat response from llm service

---

Error json payload

If the error originated from API itself, it should return json response with two fields as follows:

| Attribute   | Type                   | Description                                                                          |
|-------------|------------------------|--------------------------------------------------------------------------------------|
| error_code       | str                 |  error code (basically the class name of the error  
| detail  | str                 | error details
