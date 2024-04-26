import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from api.common.error import (
    ObjectStorageError,
    UnsupportedFileTypeError,
    ObjectStorageFileNotFoundError,
    LlmError,
    APIError,
)
from api.routers.tektome import router

logging.basicConfig(filename="app.log", encoding="utf-8", level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()


@app.exception_handler(UnsupportedFileTypeError)
async def unsupported_file_type_error_handler(
    request: Request, exc: UnsupportedFileTypeError
):
    return JSONResponse(
        status_code=400,
        content=dict(error_code=exc.__class__.__name__, detail=str(exc)),
    )


@app.exception_handler(ObjectStorageFileNotFoundError)
async def file_not_found_error_handler(
    request: Request, exc: ObjectStorageFileNotFoundError
):

    return JSONResponse(
        status_code=400,
        content=dict(error_code=exc.__class__.__name__, detail=str(exc)),
    )


@app.exception_handler(ObjectStorageError)
async def object_storage_error_handler(request: Request, exc: ObjectStorageError):

    return JSONResponse(
        status_code=500,
        content=dict(error_code=exc.__class__.__name__, detail=str(exc)),
    )


@app.exception_handler(LlmError)
async def llm_error_handler(request: Request, exc: LlmError):
    return JSONResponse(
        status_code=500,
        content=dict(error_code=exc.__class__.__name__, detail=str(exc)),
    )


@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    return JSONResponse(
        status_code=500,
        content=dict(error_code=exc.__class__.__name__, detail=str(exc)),
    )


@app.get("/")
async def root():
    return dict(hello="world")


app.include_router(router, prefix="/v1")
