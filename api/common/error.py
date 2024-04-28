class APIError(Exception):
    """
    General Error
    """

    def __init__(self, message: str = None) -> None:
        if message is None:
            message = (
                "Unexpected error. Please report to developer to investigate the issue."
            )

        super().__init__(message)


class LlmError(APIError):
    """
    General error for llm service

    Args
        - message (str): Optional message to show if it is supplied. Otherwise, the default message is used
    """

    def __init__(self, message: str = None) -> None:
        if message is None:
            message = "Unexpected error in llm service. Please report to developer to investigate the issue."

        super().__init__(message)


class LlmVectorStoreError(LlmError):
    """
    Wrapper for error from vector db
    """

    def __init__(self, message: str = None) -> None:
        if message is None:
            message = "There is some problem with vector db."

        super().__init__(message)


# Error classes that wraps around OpenAI API error
class LlmOpenAiBadRequestError(LlmError):
    """
    Wrapper for BadRequestError threw from OpenAI library
    """

    def __init__(self) -> None:
        message = "There is something wrong with OpenAI implementation on server side. Please contact developer to investigate the issue."
        super().__init__(message)


class LlmOpenAiAuthenticationError(LlmError):
    """
    Wrapper of AuthenticationError threw from OpenAI library
    """

    def __init__(self) -> None:
        message = "here is something wrong with OpenAI API key on server side. Please contact developer to investigate the issue."
        super().__init__(message)


class LlmOpenAiPermissionError(LlmError):
    """
    Wrapper of PermissionError threw from OpenAI library
    """

    def __init__(self) -> None:
        message = "There is something wrong with permission associated with OpenAI API key. Please contact developer to investigate the issue."

        super().__init__(message)


class LlmOpenAiRateLimitError(LlmError):
    """
    Wrapper of RateLimitError threw from OpenAI library
    """

    def __init__(self) -> None:
        message = "Too many requests were sent to Open AI service. Please wait or contact developer to resolve the issue."
        super().__init__(message)


class LlmOpenAiServiceError(LlmError):
    """
    Wrapper of ServiceError threw from OpenAI library
    """

    def __init__(self) -> None:
        message = "There is problem at Open AI service. Please contact developer to report the issue."
        super().__init__(message)


class LlmOpenAiAPIConnectionError(LlmError):
    """
    Wrapper of ConnectionError threw from OpenAI library
    """

    def __init__(self) -> None:
        message = "There is problem with connection to Open AI service. Please contact developer to report the issue."
        super().__init__(message)


class LlmOpenAiTimeoutError(LlmError):
    """
    Wrapper of TimeoutError threw from OpenAI library
    """

    def __init__(self) -> None:
        message = "There is timeout problem during communication with Open AI service. Please contact developer to report the issue."
        super().__init__(message)


class UnsupportedFileTypeError(APIError):
    """
    This error is threw when the content type of the upload file is not in the supported list (pdf, png, jpg, and tiff)

    Args
        - detail (str): Optional detail message that describes which file has problem if it is supplied. Otherwise, the default message is used

    """

    def __init__(self, details: str) -> None:
        super().__init__(
            f"The uploaded file(s) are not in supported format > {details}"
        )


class ObjectStorageError(APIError):
    """
    General error for object storage service

    Args
        - message (str): Optional message to show if it is supplied. Otherwise, the default message is used
    """

    def __init__(self, message: str = None) -> None:
        if message is None:
            message = "Unexpected error in object storage service. Please report to developer to investigate the issue."

        super().__init__(message)


class ObjectStorageFileNotFoundError(ObjectStorageError):
    """
    This error is threw when target file is not found on the object storage server
    """

    def __init__(self) -> None:
        super().__init__("Could not find target file")


class ObjectStorageConnectionError(ObjectStorageError):
    """
    This error is used when there is connection problem with object storage server
    """

    def __init__(self) -> None:
        super().__init__("Could not connect to object storage service")
