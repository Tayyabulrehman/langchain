import os

from dotenv import load_dotenv
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.history_aware_retriever import create_history_aware_retriever
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain.memory import ConversationBufferMemory
from langchain_community.embeddings import HuggingFaceEmbeddings, SentenceTransformerEmbeddings
from langchain_core.prompts import PromptTemplate, MessagesPlaceholder
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain.schema.runnable import Runnable
from langchain.schema.runnable.config import RunnableConfig
from typing import cast

import chainlit as cl
from langchain_pinecone import PineconeVectorStore
from langchain_postgres import PGVector
from openai import OpenAI
from pinecone import Pinecone

from utils.auth import authenticate
from utils.wraper import CustomAPIModel, get_response

load_dotenv()
embeddings = SentenceTransformerEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

user_memory_dict = {}
# vectorstore = PineconeVectorStore(
#     index_name='embedding-index-v3', embedding=embeddings,
# )

from pinecone import Pinecone

# Initialize Pinecone client and index
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
# PINECONE_NAMESPACE = os.getenv("PINECONE_NAMESPACE", "default")


pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)

# Double-check your index has data
print("🔍 Pinecone stats:", index.describe_index_stats())

# Initialize LangChain vectorstore (connected to actual index)
vector_store = PineconeVectorStore(
    index=index,  # ✅ pass the actual index object
    embedding=embeddings,
    namespace="default"
)

# Define a retriever (to search the vector database for similar documents)
# retriever = vectorstore.as_retriever(
#     search_type="similarity", search_kwargs={"k": 5, "filter":{"manager":True} },
#                                      )
llm = CustomAPIModel()


def get_session_history(session_id: str):
    return cl.user_session.get("chat_history")


@cl.password_auth_callback
def auth_callback(username: str, password: str):
    # Fetch the user matching username from your database
    # and compare the hashed password with the value stored in the database
    user = authenticate(username, password)
    if user:
        return cl.User(identifier=user.get("email"), metadata={"role": user.get("role"), "provider": "credentials"})
    else:
        return None


@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("chat_history", ChatMessageHistory())
    # cl.user_session.set("llm_chain", qa)


session_memory = {}


@cl.on_message
async def on_message(message: cl.Message):
    print(message)

    # role = cl.user_session.get("user").metadata.get("role")
    # filter = {}
    # if role=="employee":
    #     filter ={"employee": True}
    # elif role=="manager":
    #     filter = {"manager": True}
    context = results = vector_store.similarity_search(message.content, k=10,
                                                       )
    msg = cl.Message(content="")
    if context:
        context = ''.join(x.page_content for x in context)

        msg = cl.Message(content="")

        prompt_template = """You are an assistant for question-answering tasks.
    Use the following documents to answer the question.
    If you don't know the answer, just say that you don't know.
    Use three sentences maximum and keep the answer concise:
    Question: {question}
    Documents: {documents}
    Answer:
    """.format(documents=context, question=message.content)

        response = get_response(prompt_template)
    else:
        response = "Sorry, I couldn't find any relevant information for your query" \
                   ". Could you please rephrase or try another question?"
    await msg.stream_token(response or "")
    await msg.send()


if __name__ == "__main__":
    from chainlit.cli import run_chainlit

    run_chainlit(__file__)
