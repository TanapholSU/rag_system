import os

from api.service.llm.gpt35 import Gpt35LLMService
from api.service.llm import load_ocr_json_result
from config import app_config


def test_import_docs():
    """
    Test import document to qdrant vector database (in-memory mode).
    If the document splitting task is working properly, the number of documents should be greater than one
    """
    llm = Gpt35LLMService(
        openai_api_key=app_config.openai_api_key,
        vector_db_url=":memory:",
        vector_db_collection_name="tektome",
        text_split_chunk_size=128,
        text_split_chunk_overlap=20,
        vector_search_top_k=5,
    )

    docs = load_ocr_json_result(
        os.path.join("test_files", "ocr", "東京都建築安全条例.json"),
        source_name="file1",
    )

    llm.import_docs_to_vector_store(docs)

    # number original documents should be one
    assert len(docs) == 1

    # after splitted and stored in llm the number should be greater than original
    assert llm.qdrant_client.count("tektome") != len(docs)


def test_import_multiple_docs():
    """
    Test import multiple documents to qdrant vector database (in-memory mode).
    Then, we check whether the metadata contains original filename and they are nothing changed after we import each file
    """

    llm = Gpt35LLMService(
        openai_api_key=app_config.openai_api_key,
        vector_db_url=":memory:",
        vector_db_collection_name="tektome",
        text_split_chunk_size=128,
        text_split_chunk_overlap=20,
        vector_search_top_k=5,
    )

    docs = load_ocr_json_result(
        os.path.join("test_files", "ocr", "東京都建築安全条例.json"),
        source_name="file1",
    )

    llm.import_docs_to_vector_store(docs)

    total_docs = llm.qdrant_client.count("tektome").count
    docs, _ = llm.qdrant_client.scroll("tektome", limit=total_docs)

    documents1_ids_list = []
    for d in docs:
        documents1_ids_list.append(d.id)
        assert d.payload["metadata"]["source"] == "file1"

    docs = load_ocr_json_result(
        os.path.join("test_files", "ocr", "東京都建築安全条例.json"),
        source_name="file2",
    )

    llm.import_docs_to_vector_store(docs)

    total_docs = llm.qdrant_client.count("tektome").count
    docs, _ = llm.qdrant_client.scroll("tektome", limit=total_docs)

    for d in docs:

        if d.id in documents1_ids_list:
            assert d.payload["metadata"]["source"] == "file1"
            continue

        assert d.payload["metadata"]["source"] == "file2"


def test_query():
    """
    Function to test query with the tokyo building safety content.
    The LLM should return string response which contains date
    """
    llm = Gpt35LLMService(
        openai_api_key=app_config.openai_api_key,
        vector_db_url=":memory:",
        vector_db_collection_name="tektome",
        text_split_chunk_size=128,
        text_split_chunk_overlap=20,
        vector_search_top_k=5,
    )

    docs = load_ocr_json_result(
        os.path.join("test_files", "ocr", "東京都建築安全条例.json"),
        source_name="file1",
    )

    llm.import_docs_to_vector_store(docs)

    query = "When Tokyo Building Safety Regulation is made"
    result = llm.query(query, "file1")

    assert isinstance(result, str)
    assert len(result) > 0

    # TODO: find better way to check the relevancy of the output because output is non-deterministic
    keywords = ["December", "1950", "Showa 25", "7"]
    found_relevant_keyword = any([True if k in result else False for k in keywords])
    assert found_relevant_keyword == True

    query = "When Tokyo Building Safety Regulation is made"
    result = llm.query(query, "file_not_exist")
    keywords = ["December", "1950", "Showa 25", "7"]
    found_relevant_keyword = any([True if k in result else False for k in keywords])
    assert found_relevant_keyword == False
