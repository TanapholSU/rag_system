import logging
from typing import BinaryIO
from minio import Minio
from urllib3.exceptions import MaxRetryError
from api.common.error import (
    ObjectStorageConnectionError,
    ObjectStorageError,
    ObjectStorageFileNotFoundError,
)
from api.service.storage import ObjectStorage, prepend_unique_id_to_filename
from base64 import b64encode
from datetime import timedelta

logger = logging.getLogger(__name__)


class MinioStorage(ObjectStorage):

    def __init__(
        self,
        endpoint: str,
        bucket_name: str,
        access_key: str,
        secret_key: str,
        secure: bool = False,
    ) -> None:
        self.bucket_name = bucket_name
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )

        try:
            found = self.client.bucket_exists(self.bucket_name)
            if not found:
                self.client.make_bucket(self.bucket_name)

        except MaxRetryError as err:
            logger.exception("Could not connect to object storage")
            raise ObjectStorageConnectionError from err

        except Exception as err:
            logger.exception("Got exception from object storage")
            raise ObjectStorageError from err

    def upload(
        self,
        filename: str,
        file_data: BinaryIO,
        file_length_in_bytes: int = -1,
        part_size_in_bytes: int = 10 * 1024 * 1024,
        append_uuid_to_filename: bool = True,
    ) -> str:

        metadata = dict(encoded_original_filename=b64encode(filename.encode()).decode())

        if append_uuid_to_filename:
            stored_filename = prepend_unique_id_to_filename(filename)
        else:
            stored_filename = filename

        try:
            if file_length_in_bytes == -1:
                self.client.put_object(
                    self.bucket_name,
                    stored_filename,
                    file_data,
                    length=file_length_in_bytes,
                    part_size=part_size_in_bytes,
                    metadata=metadata,
                )
            else:
                self.client.put_object(
                    self.bucket_name,
                    stored_filename,
                    file_data,
                    file_length_in_bytes,
                    metadata=metadata,
                )

            return self._get_signed_url(stored_filename)

        except MaxRetryError as err:
            logger.exception("Could not connect to object storage")
            raise ObjectStorageConnectionError from err

        except Exception as err:
            logger.exception("Got exception from object storage")
            raise ObjectStorageError from err

    def contains_file(self, stored_filename: str) -> bool:
        try:
            self.client.stat_object(self.bucket_name, stored_filename)
            return True

        except MaxRetryError as err:
            raise ObjectStorageConnectionError from err

        except Exception as err:
            if "NoSuchKey" in str(err):
                return False

            raise ObjectStorageFileNotFoundError

    def delete(self, stored_filename: str) -> bool:
        try:
            if not self.contains_file(stored_filename):
                return False

            self.client.remove_object(self.bucket_name, stored_filename)

            return True

        except MaxRetryError as err:
            raise ObjectStorageConnectionError from err

        except Exception as err:
            raise ObjectStorageError from err

    def _get_signed_url(self, stored_filename: str) -> str:
        """
        Private function for getting dummy signed URL for the target file in the bucket

        Args:
            - stored_file_name:  filename in the bucket

        Returns:
            - signed url. In this implementation it is url for HEAD operation only.
             This is because ocr endpoint is just a mock.
             So, there is no need to pull actual file from bucket for processing ocr)
        """

        return self.client.get_presigned_url("HEAD", self.bucket_name, stored_filename)
