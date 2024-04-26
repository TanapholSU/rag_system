import os
from uuid import uuid4
from abc import ABC, abstractmethod
from typing import BinaryIO


class ObjectStorage(ABC):

    @abstractmethod
    def upload(
        self,
        filename: str,
        file_pointer: BinaryIO,
        file_length_in_bytes: int = -1,
        part_size_in_bytes: int = 10 * 1024 * 1024,
        append_uuid_to_filename: bool = True,
    ) -> str:
        """
        This function uploads the requested file to object storage

        Args:
            - filname: the name of the file to be stored in object storage
            - file_pointer: the BinaryIO stream of the local file to be uploaded
            - file_length_in_bytes: file size in bytes. if unknown, value should be set to -1 and the part_size_in_bytes should be set
            - part_size_in_bytes: Normally the file is readed in chunks. This parameters will be used as maximum amount of bytes in each chunk. Default value is 10MB
            - append_uuid_to_filename: Default value is True. It means the uuid is attached to the stored filename to prevent collision in object storage.

        Returns:
            - signed URL of the uploaded file

        Raises:
            - ObjectStorageError if there is problem with the object storage service or connection
        """
        pass

    @abstractmethod
    def contains_file(self, stored_filename: str) -> bool:
        """
        Utility function to check whether the file name does exist in the object storage

        Args:
            - stored_filename: input filename

        Returns:
            - True if it exits. Otherwise, False is retruned.
        """
        pass

    @abstractmethod
    def delete(self, stored_filename: str) -> bool:
        """
        Function to delete target file in the object storage
            - stored_filename: the filename in the object storage

        Returns:
            True if operation is success. Otherwise, False is returned

        """
        pass


def prepend_unique_id_to_filename(data: str):
    basename = os.path.basename(data)
    uuid = uuid4()
    return f"{uuid}_{basename}"
