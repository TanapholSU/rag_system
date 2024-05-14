import os
import traceback
from urllib.parse import unquote, urlparse
from api.common.error import ObjectStorageFileNotFoundError

ALLOWED_FILE_FORMAT = ["image/tiff", "image/jpeg", "image/png", "application/pdf"]


def is_allowed_content_type(mime_type: str) -> bool:
    """
    Function to check the file type (based on mime_type string from FileUpload)

    Args
        - mime_type: mime type obtained from FileUpload object

    Returns:
        - True if file in the allowed file type (tiff, jpeg, png, or pdf). Otherwise, False is returned
    """

    if mime_type.lower() in ALLOWED_FILE_FORMAT:
        return True

    return False


def get_filename_from_signed_url(signed_url: str) -> str:
    """
    Function to get the original file name from the encoded & signed url returned from upload endpoint

    Args:
        - signed_url: the signed url obtained from upload endpoint

    Returns:
        - The file name of the file stored in the object storage

    """
    unquoted_url = unquote(signed_url)
    parsed_url = urlparse(unquoted_url)
    output = os.path.basename(parsed_url.path)

    if output is None or output.strip() == "":
        raise ObjectStorageFileNotFoundError

    return os.path.basename(parsed_url.path)


def get_traceback_str(exc: Exception, debug=False) -> str:
    if debug:
        traceback_str = "".join(
            traceback.format_exception(exc, value=exc, tb=exc.__traceback__)
        )

        return f"{str(exc)}: {traceback_str}"

    return str(exc)
