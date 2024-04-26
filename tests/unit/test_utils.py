from api.common.utils import (
    get_filename_from_signed_url,
    is_allowed_content_type,
    ALLOWED_FILE_FORMAT,
)


def test_get_filename_from_signed_url():
    url = "http://127.0.0.1:9000/tektome/3a5d030a-847f-4622-ac0e-cf6119bd7336_%E6%9D%B1%E4%BA%AC%E9%83%BD%E5%BB%BA%E7%AF%89%E5%AE%89%E5%85%A8%E6%9D%A1%E4%BE%8B.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=4J5ERONJLHONGMYH2LMZ%2F20240425%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20240425T073616Z&X-Amz-Expires=43200&X-Amz-Security-Token=eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3NLZXkiOiI0SjVFUk9OSkxIT05HTVlIMkxNWiIsImV4cCI6MTcxNDA3MTYwNSwicGFyZW50Ijoicm9vdCJ9.psKv2K9j0nXkDTyMRt4EpaWTLycMQjohI4CXEjgJRpqSJyYbTuuUVYHTAfqNrkMa6OA4xGbcw_5JOVECYqRxwQ&X-Amz-SignedHeaders=host&versionId=null&X-Amz-Signature=d8d1cf9282ea1a03da295c139aae62af8b98136818c031ad80525f890dd41ea7"
    result = get_filename_from_signed_url(url)
    assert result == "3a5d030a-847f-4622-ac0e-cf6119bd7336_東京都建築安全条例.pdf"


def test_is_allowed_content_type():
    for supported_mime_type in ALLOWED_FILE_FORMAT:
        assert is_allowed_content_type(supported_mime_type) == True

    assert is_allowed_content_type("application/video") == False
