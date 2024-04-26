import logging
import openai
import qdrant_client
from qdrant_client.http.models import Distance, VectorParams
from langchain_core.exceptions import LangChainException
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_core.vectorstores import VectorStoreRetriever
from langchain.vectorstores.qdrant import Qdrant
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers.string import StrOutputParser
from typing import List
from api.service.llm import LLMService
from api.common.error import (
    LlmError,
    LlmOpenAiAPIConnectionError,
    LlmOpenAiPermissionError,
    LlmOpenAiAuthenticationError,
    LlmOpenAiBadRequestError,
    LlmOpenAiRateLimitError,
    LlmOpenAiServiceError,
)


logger = logging.getLogger(__name__)


class Gpt35LLMService(LLMService):

    VECTOR_DIMENSIONS = 1536

    def __init__(
        self,
        openai_api_key: str,
        vector_db_url: str,
        vector_db_collection_name: str,
        text_split_chunk_size: int,
        text_split_chunk_overlap: int,
        vector_search_top_k: int,
    ) -> None:
        self.key = openai_api_key
        self.embedding = OpenAIEmbeddings(api_key=self.key)
        self.qdrant_client = qdrant_client.QdrantClient(vector_db_url)

        self.text_split_chunk_size = text_split_chunk_size
        self.text_split_chunk_overlap = text_split_chunk_overlap

        self.vector_search_top_k = vector_search_top_k

        if not self.qdrant_client.collection_exists(
            collection_name=vector_db_collection_name
        ):
            try:
                self.qdrant_client.create_collection(
                    vector_db_collection_name,
                    vectors_config=VectorParams(
                        size=self.VECTOR_DIMENSIONS, distance=Distance.COSINE
                    ),
                )
            except:
                pass

            logger.info("Created a collection in vector database")

        self.vector_store: Qdrant = Qdrant(
            client=self.qdrant_client,
            collection_name=vector_db_collection_name,
            embeddings=self.embedding,
        )

    def import_docs_to_vector_store(self, docs: List[Document]):
        try:
            logger.debug("Splitting document")
            docs = self._split_texts(docs)

            logger.debug("Adding the splitted document to vector db")
            self.vector_store.add_documents(docs)

        except openai.APIConnectionError as err:
            raise LlmOpenAiAPIConnectionError from err

        except openai.BadRequestError as err:
            raise LlmOpenAiBadRequestError from err

        except openai.AuthenticationError as err:
            raise LlmOpenAiAuthenticationError from err

        except openai.PermissionDeniedError as err:
            raise LlmOpenAiPermissionError from err

        except openai.RateLimitError as err:
            raise LlmOpenAiRateLimitError from err

        except openai.APIError as err:
            raise LlmOpenAiServiceError from err

        except LangChainException as err:
            raise LlmError(
                "(LangChain) There is problem with our llm service. Please report the issue to developer"
            ) from err

        except Exception as err:
            raise LlmError(
                "Encountered unexpected error from LLM service. Please report the issue to developer"
            ) from err

    def query(self, query: str, filename: str) -> str:
        try:
            hit_results = self._retrieve_docs(query, filename)
            logger.debug(f"Got {len(hit_results)} context results from vector db")

            template = """Answer the question based only on the following context:
                {context}
                Question: {question}
                """

            prompt = ChatPromptTemplate.from_template(template)
            llm = ChatOpenAI(model_name="gpt-3.5-turbo", api_key=self.key)
            chain = prompt | llm | StrOutputParser()

            return chain.invoke({"question": query, "context": hit_results})

        except openai.APIConnectionError as err:
            raise LlmOpenAiAPIConnectionError from err

        except openai.BadRequestError as err:
            raise LlmOpenAiBadRequestError from err

        except openai.AuthenticationError as err:
            raise LlmOpenAiAuthenticationError from err

        except openai.PermissionDeniedError as err:
            raise LlmOpenAiPermissionError from err

        except openai.RateLimitError as err:
            raise LlmOpenAiRateLimitError from err

        except openai.APIError as err:
            raise LlmOpenAiServiceError from err

        except LangChainException as err:
            raise LlmError(
                "(LangChain) There is problem with our llm service. Please report the issue to developer"
            ) from err

        except Exception as err:
            raise LlmError(
                "Encountered unexpected error from LLM service. Please report the issue to developer"
            ) from err

    def _split_texts(self, docs: List[Document]) -> List[Document]:

        text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            model_name="gpt-3.5-turbo",
            chunk_size=self.text_split_chunk_size,
            chunk_overlap=self.text_split_chunk_overlap,
        )

        return text_splitter.split_documents(docs)

    def _retrieve_docs(self, query: str, filename: str) -> List[Document]:
        retriever: VectorStoreRetriever = self.vector_store.as_retriever(
            search_kwargs=dict(k=self.vector_search_top_k, filter=dict(source=filename))
        )

        return retriever.get_relevant_documents(query)
