import os

from langchain_community.document_loaders.json_loader import JSONLoader
from langchain_core.documents import Document
from abc import ABC, abstractmethod
from typing import List


# Define the metadata extraction function.
def gen_metadata_func(file_id: str):
    def metadata_func(record: dict, metadata: dict) -> dict:
        metadata["source"] = file_id

        return metadata

    return metadata_func


def load_ocr_json_result(file_path: str, source_name=None) -> List[Document]:
    """
    This function load json result (file) obtained from mock ocr service

    Args:
        - file_path: path of json ocr result

    Returns:
        - List of documents
    """
    if source_name is None:
        source_name = os.path.basename(file_path)

    loader = JSONLoader(
        file_path=file_path,
        jq_schema=".analyzeResult.content",
        text_content=False,
        metadata_func=gen_metadata_func(source_name),
    )
    docs = loader.load()
    return docs


class LLMService(ABC):

    @abstractmethod
    def import_docs_to_vector_store(
        self, docs: List[Document], **kwargs
    ) -> List[Document]:
        """
        This is main function to import the document extracted from json ocr result to vector database

        Args:
            - docs: list of Documents

        Returns:
            - list of spliited documents

        Raises:
            - LLMError family if there is problem with the openai or langchain
        """
        pass

    @abstractmethod
    def query(self, query_string: str, filename: str) -> str:
        """
        Query function for RAG system.
        This function searchs for documents extracted from the file of the input signed URL.
        The returned value is the response string obtained from LLM

        Args:
            - query_string: input query
            - filename: the target filename

        Returns:
            - string response from LLM

        Raises:
            - LLMError family if there is problem with the openai or langchain
        """
        pass

    @abstractmethod
    def _split_texts(self, docs: List[Document], **kwargs) -> List[Document]:
        """
        Private function to split original document to smaller chunks
        Args:
            - docs: list of Documents

        Returns:
            - list of spliited documents
        """
        pass

    @abstractmethod
    def _get_retriever(self, filename: str, top_k=1) -> List[Document]:
        """
        Private function to get vector db retriever with filename filtering

        Args:
            - query_string: input query
            - filename: the target filename
            - top_k (optional): the number of the top-k most relevant documents to be retrieved

        Returns:
            - retriever for the target file
        """
        pass
