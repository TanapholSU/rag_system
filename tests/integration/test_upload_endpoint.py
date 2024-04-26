import os
import requests

from fastapi.testclient import TestClient
from fastapi import status
from main import app
from api.schemas.upload import UploadListResponse

client = TestClient(app)

sample_files_md5 = {
    "建築基準法施行令.pdf": "be5b625ae79945b5257ccc30a321e984",
    "東京都建築安全条例.pdf": "99ef153b76c24ee4703f3b9e025bab09",
    "tektome.jpg": "e8e2a41d7a692deaa81e3d7cf2bf908a",
    "tektome.png": "72a1655ac1422150b9f2ec6f212f8706",
    "tektome.tif": "e28e41711be81f288e49ae32b81c2f06",
}


def clean_quote_from_etag(etag):
    return etag[1:-1]


def test_upload_one_pdf_file():
    """
    Test upload one valid pdf file.
    Endpoint should accept and the md5 of local and uploaded file are identical
    """

    files = [
        (
            "files",
            open(os.path.join("test_files", "sample", "建築基準法施行令.pdf"), "rb"),
        )
    ]

    response = client.post(url="/v1/upload", files=files)

    assert response.status_code == status.HTTP_200_OK

    response = response.json()
    upload_list_data = UploadListResponse(**response)

    assert len(upload_list_data.upload_results) == 1
    assert upload_list_data.upload_results[0].filename == "建築基準法施行令.pdf"
    url = upload_list_data.upload_results[0].signed_url

    # check md5 of the uploaded file
    result = requests.head(url)
    md5 = result.headers["ETAG"]

    # clean quote character from etag
    assert sample_files_md5["建築基準法施行令.pdf"] == clean_quote_from_etag(md5)


def test_upload_jpeg_file():
    """
    Test upload one valid jpeg file.
    Endpoint should accept and the md5 of local and uploaded file are identical
    """
    files = [("files", open(os.path.join("test_files", "tektome.jpg"), "rb"))]

    response = client.post(url="/v1/upload", files=files)

    assert response.status_code == status.HTTP_200_OK

    response = response.json()
    upload_list_data = UploadListResponse(**response)

    assert len(upload_list_data.upload_results) == 1
    assert upload_list_data.upload_results[0].filename == "tektome.jpg"
    url = upload_list_data.upload_results[0].signed_url

    # check md5 of the uploaded file
    result = requests.head(url)
    md5 = result.headers["ETAG"]

    # clean quote character from etag
    assert sample_files_md5["tektome.jpg"] == clean_quote_from_etag(md5)


def test_upload_png_file():
    """
    Test upload one valid png file.
    Endpoint should accept and the md5 of local and uploaded file are identical
    """
    files = [("files", open(os.path.join("test_files", "tektome.png"), "rb"))]

    response = client.post(url="/v1/upload", files=files)

    assert response.status_code == status.HTTP_200_OK

    response = response.json()
    upload_list_data = UploadListResponse(**response)

    assert len(upload_list_data.upload_results) == 1
    assert upload_list_data.upload_results[0].filename == "tektome.png"
    url = upload_list_data.upload_results[0].signed_url
    # check md5 of the uploaded file
    result = requests.head(url)
    md5 = result.headers["ETAG"]

    # clean quote character from etag
    assert sample_files_md5["tektome.png"] == clean_quote_from_etag(md5)


def test_upload_tiff_file():
    """
    Test upload one valid tiff file.
    Endpoint should accept and the md5 of local and uploaded file are identical
    """
    files = [("files", open(os.path.join("test_files", "tektome.tif"), "rb"))]

    response = client.post(url="/v1/upload", files=files)

    assert response.status_code == status.HTTP_200_OK

    response = response.json()
    upload_list_data = UploadListResponse(**response)

    assert len(upload_list_data.upload_results) == 1
    assert upload_list_data.upload_results[0].filename == "tektome.tif"
    url = upload_list_data.upload_results[0].signed_url

    # check md5 of the uploaded file
    result = requests.head(url)
    md5 = result.headers["ETAG"]

    # clean quote character from etag
    assert sample_files_md5["tektome.tif"] == clean_quote_from_etag(md5)


def test_upload_multiple_files():
    """
    Test upload multiple (but valid) files.
    Endpoint should accept and the md5 of the same file in local and object storage should be match
    """
    files = [
        (
            "files",
            open(os.path.join("test_files", "sample", "建築基準法施行令.pdf"), "rb"),
        ),
        (
            "files",
            open(os.path.join("test_files", "sample", "東京都建築安全条例.pdf"), "rb"),
        ),
        ("files", open(os.path.join("test_files", "tektome.jpg"), "rb")),
        ("files", open(os.path.join("test_files", "tektome.png"), "rb")),
        ("files", open(os.path.join("test_files", "tektome.tif"), "rb")),
    ]

    response = client.post(url="/v1/upload", files=files)

    assert response.status_code == status.HTTP_200_OK

    response = response.json()
    upload_list_data = UploadListResponse(**response)

    assert len(upload_list_data.upload_results) == 5
    assert upload_list_data.upload_results[0].filename == "建築基準法施行令.pdf"
    assert upload_list_data.upload_results[1].filename == "東京都建築安全条例.pdf"
    assert upload_list_data.upload_results[2].filename == "tektome.jpg"
    assert upload_list_data.upload_results[3].filename == "tektome.png"
    assert upload_list_data.upload_results[4].filename == "tektome.tif"

    url = upload_list_data.upload_results[0].signed_url
    # check md5 of the uploaded file
    result = requests.head(url)
    md5 = result.headers["ETAG"]
    assert sample_files_md5["建築基準法施行令.pdf"] == clean_quote_from_etag(md5)

    url = upload_list_data.upload_results[1].signed_url
    result = requests.head(url)
    md5 = result.headers["ETAG"]
    assert sample_files_md5["東京都建築安全条例.pdf"] == clean_quote_from_etag(md5)

    url = upload_list_data.upload_results[2].signed_url
    result = requests.head(url)
    md5 = result.headers["ETAG"]
    assert sample_files_md5["tektome.jpg"] == clean_quote_from_etag(md5)

    url = upload_list_data.upload_results[3].signed_url
    result = requests.head(url)
    md5 = result.headers["ETAG"]
    assert sample_files_md5["tektome.png"] == clean_quote_from_etag(md5)

    url = upload_list_data.upload_results[4].signed_url
    result = requests.head(url)
    md5 = result.headers["ETAG"]
    assert sample_files_md5["tektome.tif"] == clean_quote_from_etag(md5)


def test_upload_file_with_unsupported_type():
    """
    Test upload unsupported file.
    Endpoint should return BadRequest error and proper message
    """
    files = [
        ("files", open("main.py", "rb")),
    ]

    response = client.post(url="/v1/upload", files=files)

    assert response.status_code == status.HTTP_400_BAD_REQUEST

    response = response.json()
    response["error_code"] = "UnsupportedFileTypeError"
    response["detail"] = "The uploaded file(s) are not in supported format main.py"


def test_upload_multiple_files_with_unsupported_type():
    """
    Test upload multiple files but some files are unsupported.
    Endpoint should return BadRequest error and proper message
    """
    files = [
        (
            "files",
            open(os.path.join("test_files", "sample", "建築基準法施行令.pdf"), "rb"),
        ),
        ("files", open("main.py", "rb")),
        (
            "files",
            open(os.path.join("test_files", "sample", "東京都建築安全条例.pdf"), "rb"),
        ),
        ("files", open("config.py", "rb")),
    ]

    response = client.post(url="/v1/upload", files=files)

    assert response.status_code == status.HTTP_400_BAD_REQUEST

    response = response.json()
    response["error_code"] = "UnsupportedFileTypeError"
    response["detail"] = (
        "The uploaded file(s) are not in supported format main.py, config.py"
    )
