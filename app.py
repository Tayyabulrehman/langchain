import os
import re

from operator import index

from dotenv import load_dotenv
from pinecone import Pinecone
from utils.wraper import ChatGPTModel

from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain.memory import ConversationBufferMemory
from langchain_community.embeddings import HuggingFaceEmbeddings, SentenceTransformerEmbeddings, OpenAIEmbeddings
from langchain_core.prompts import PromptTemplate, MessagesPlaceholder
from langchain_community.chat_message_histories import ChatMessageHistory

# import chainlit as cl
# from langchain_pinecone import PineconeVectorStore
#
#
# from utils.auth import authenticate
# from utils.wraper import CustomAPIModel, get_response, ChatGPTModel
#
# load_dotenv()
#
# PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY')
# OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
# os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
#
# pc = Pinecone(api_key=PINECONE_API_KEY)
# index_name = "rag"
# index = pc.Index(index_name)
#
#
# from langchain.chains import RetrievalQA
# llm = ChatGPTModel(model_name="gpt-4-turbo")
# # Initialize Pinecone vector store
# embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
# vectorstore = PineconeVectorStore(index=index, embedding=embeddings)
# retriever = vectorstore.as_retriever(search_type="similarity")
#
# def get_session_history(session_id: str):
#     return cl.user_session.get("chat_history")
#
#
# @cl.password_auth_callback
# def auth_callback(username: str, password: str):
#     # Fetch the user matching username from your database
#     # and compare the hashed password with the value stored in the database
#     user = authenticate(username, password)
#     if user:
#         return cl.User(identifier=user.get("email"), metadata={"role": user.get("role"), "provider": "credentials"})
#     else:
#         return None
#
#
# @cl.on_chat_start
# async def on_chat_start():
#     cl.user_session.set("chat_history", ChatMessageHistory())
#     # cl.user_session.set("llm_chain", qa)
#
#
# session_memory = {}
#
#
# @cl.on_message
# async def on_message(message: cl.Message):
#     print(message)
#
#     # role = cl.user_session.get("user").metadata.get("role")
#     # filter = {}
#     # if role=="employee":
#     #     filter ={"employee": True}
#     # elif role=="manager":
#     #     filter = {"manager": True}
#     # context = results = vector_store.similarity_search(message.content, k=10,
#     #                                                    )
#     msg = cl.Message(content="")
#     # if context:
#     #     context = ''.join(x.page_content for x in context)
#     #
#     #     msg = cl.Message(content="")
#
#     prompt_template = """You are an assistant for question-answering tasks.
#     Use the following documents to answer the question.
#     If you don't know the answer, just say that you don't know.
#     Use three sentences maximum and keep the answer concise:
#     Question: {question}
#     Answer:
#     """.format(question=message.content)
#     qa = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever, return_source_documents=True)
#     # Query the model
#     # prompt = "AI Agents vs. Agentic AI"
#     result = qa({"query": prompt_template})
#     response=result.get("result")
#     await msg.stream_token(response or "")
#     await msg.send()
#
#
# if __name__ == "__main__":
#     from chainlit.cli import run_chainlit
#
#     run_chainlit(__file__)

import os
import chainlit as cl
from dotenv import load_dotenv
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain.chains import RetrievalQA
from langchain.memory import ChatMessageHistory

load_dotenv()

PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index("rag")
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)
# Embeddings + Vectorstore
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")



from urllib.parse import urlparse, parse_qs

vectorstore = PineconeVectorStore(index=index, embedding=embeddings)
retriever = vectorstore.as_retriever(search_type="similarity")


@cl.on_chat_start
async def on_chat_start():
    """
    Extract query params from URL:
    Example: http://localhost:8000/?user=12
    """
    path = cl.user_session.get("http_referer")
    m = re.search(r'[?&]?user=(\d+)', path or "")
    user_id = int(m.group(1)) if m else None
    print(f"user_id={user_id}")
    cl.user_session.set("user_id", user_id)
    cl.user_session.set("chat_history", ChatMessageHistory())

    # await cl.Message(content=f"Token received: {token}").send()


@cl.on_message
async def on_message(message: cl.Message):
    user_id = cl.user_session.get("user_id")
    print(f"on_message user_id={user_id}")

    if not user_id:
        await cl.Message(content="No user ID found in URL! Please excess the chatbot using admin panel").send()
        return

    msg = cl.Message(content="")

    vectorstore = PineconeVectorStore(
        index=index,
        embedding=embeddings,
    )

    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={
            # "k": 5,
            "filter": {"user_id": user_id}
        }
    )
    # retriever.get_relevant_documents

    prompt_template = """You are an assistant for question-answering tasks.
Use the following documents to answer the question.
If you don't know the answer, just say that you don't know.
Use three sentences maximum and keep the answer concise:
Question: {question}
Context: {context}
Answer:"""

    from langchain.prompts import PromptTemplate
    from langchain.chains import RetrievalQA

    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["question", "context"]
    )

    qa = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt}
    )

    # Query with just the user's question
    result = qa({"query": message.content})
    response = result.get("result")

    await msg.stream_token(response or "")
    await msg.send()

if __name__ == "__main__":
    from chainlit.cli import run_chainlit

    run_chainlit(__file__)
