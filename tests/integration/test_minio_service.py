import os
from urllib.parse import urlparse

from config import app_config
from api.service.storage.minio_storage import MinioStorage

sample_files_md5 = {
    "建築基準法施行令.pdf": "be5b625ae79945b5257ccc30a321e984",
    "東京都建築安全条例.pdf": "99ef153b76c24ee4703f3b9e025bab09",
    "tektome.jpg": "e8e2a41d7a692deaa81e3d7cf2bf908a",
    "tektome.png": "72a1655ac1422150b9f2ec6f212f8706",
    "tektome.tif": "e28e41711be81f288e49ae32b81c2f06",
}


object_storage = MinioStorage(
    endpoint=app_config.storage_service_endpoint,
    bucket_name=app_config.storage_bucket_name,
    access_key=app_config.storage_access_key,
    secret_key=app_config.storage_secret_key,
    secure=app_config.storage_secure_connection,
)


def test_upload_file():
    """
    Test case for uploading sample file.
    The md5 of local and uploaded file should be identical.
    """
    try:
        object_storage.client.remove_object(
            app_config.storage_bucket_name, "test_upload_file.jpg"
        )
    except:
        pass

    with open(os.path.join("test_files", "tektome.jpg"), "rb") as fp:
        signed_url = object_storage.upload("test_upload_file.jpg", file_data=fp)
        url = urlparse(signed_url)
        stored_filename = os.path.basename(url.path)

        data = object_storage.client.stat_object(
            app_config.storage_bucket_name, stored_filename
        )
        assert sample_files_md5["tektome.jpg"] == data.etag


def test_contains_existing_file():
    """
    Test case for testing contains_file function with existing file in object storage
    """

    with open(os.path.join("test_files", "tektome.jpg"), "rb") as fp:
        signed_url = object_storage.upload("test_upload_file.jpg", file_data=fp)
        url = urlparse(signed_url)
        stored_filename = os.path.basename(url.path)

        # if it does not exist, it will raise error here
        object_storage.client.stat_object(
            app_config.storage_bucket_name, stored_filename
        )
        assert object_storage.contains_file(stored_filename) == True


def test_contains_non_existence_file():
    """
    Test case for testing contains_file function when the file does not exist in object storage
    """
    assert object_storage.contains_file("non_existed_file.jpg") == False


def test_delete_file():
    """
    Test case for testing delete function.
    The result of contains file before and after delete operation should be True and False, respectively
    """
    with open(os.path.join("test_files", "tektome.jpg"), "rb") as fp:
        signed_url = object_storage.upload("test_upload_file.jpg", file_data=fp)
        url = urlparse(signed_url)
        stored_filename = os.path.basename(url.path)

        assert object_storage.contains_file(stored_filename) == True

        object_storage.delete(stored_filename)
        assert object_storage.contains_file(stored_filename) == False


def test_delete_non_existence_file():
    """
    Test case for testing delete function when file does not exist in object storage.
    """
    object_storage.delete("random_filename.pdf")
    assert object_storage.contains_file("random_filename.pdf") == False
