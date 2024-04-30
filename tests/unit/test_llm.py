import os
from api.service.llm import gen_metadata_func, load_ocr_json_result


def test_gen_metadata_function():
    """
    Test generate metadata function.
    The function should generate a function which returns an dictionary.
    The returned result obtained from generated function should contain the input filename
    """
    func = gen_metadata_func("file101")
    result = func({}, {})
    assert result["source"] == "file101"


def test_load_ocr_json_result():
    """
    Test json parser function.
    The number of loaded documents obtained from the function should be one.
    """
    # import json document
    docs = load_ocr_json_result(
        os.path.join("test_files", "ocr", "東京都建築安全条例.json"),
        source_name="東京都建築安全条例.pdf",
    )

    assert len(docs) == 1
