from django.conf import settings
from langchain_openai import OpenAIEmbeddings
from langchain.schema.messages import AIMessage, HumanMessage
from qdrant_client import models, QdrantClient

from assistant.langchain.lawsuits import document_chain
from assistant.langchain.qdrant_client import CustomQdrantClient


def generate_response_langchain(question, category, country, history=[]):
    payload = {}
    if category:
        payload["category"] = category

    embedding = OpenAIEmbeddings(api_key=settings.OAI_KEY)
    q_client = QdrantClient(url=settings.QDRANT_URL)
    qdrant_client = CustomQdrantClient(q_client, country.upper(), embedding)
    query_filter = None
    if payload:
        query_filter = models.Filter(
            must=[models.FieldCondition(
                key=k,
                match=models.MatchValue(value=v)
            ) for k, v in payload.items()]
        )

    user_chat_history = []
    for message in history:
        user_chat_history.extend([
            HumanMessage(content=message['user']),
            AIMessage(content=message['ai']),
        ])

    # q_embeddings = embedding.embed_query(question)
    # docs = qdrant_client.similarity_search_by_vector(q_embeddings, 3, query_filter)
    docs = qdrant_client.similarity_search(question, 3, query_filter)
    ans = document_chain.invoke(
        {"input": question, 'context': docs, 'chathistory': user_chat_history})

    return ans
