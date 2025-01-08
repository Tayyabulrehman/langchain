import os

from dotenv import load_dotenv
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.history_aware_retriever import create_history_aware_retriever
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain.memory import ConversationBufferMemory
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.prompts import PromptTemplate, MessagesPlaceholder
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_ollama import OllamaLLM
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

from utils.auth import authenticate
from utils.retriever import create_role_based_retriever
from utils.wraper import CustomAPIModel

load_dotenv()
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

user_memory_dict = {}
# vectorstore = PineconeVectorStore(
#     index_name='embedding-index-v3', embedding=embeddings,
# )


vectorstore = PGVector(
    embeddings=embeddings,
    collection_name=os.getenv("collection_name"),
    connection=os.getenv("connection"),
    use_jsonb=True,
)

def get_user_role():
    # Fetch the user's role from their session metadata
    return cl.user_session.get("user").metadata.get("role")


# Define a retriever (to search the vector database for similar documents)
llm = OllamaLLM(model="llama3.1")

contextualize_q_system_prompt = """Given a chat history and the latest user question \
which might reference context in the chat history, formulate a standalone question \
which can be understood without the chat history. Do NOT answer the question, \
just reformulate it if needed and otherwise return it as is."""
contextualize_q_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)


### Answer question ###
qa_system_prompt = """You are an assistant for question-answering tasks. \
Use the following pieces of retrieved context to answer the question. \
If you don't know the answer, just say that you don't know. \
Use three sentences maximum and keep the answer concise.\

{context}"""
qa_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", qa_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)
question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)



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
    # chain = cl.user_session.get("llm_chain")
    user_role = get_user_role()

    # Recreate the retriever with role-based filtering
    retriever = create_role_based_retriever(vectorstore, user_role)

    # Create a role-aware RAG chain dynamically
    history_aware_retriever = create_history_aware_retriever(
        llm,
        retriever,
        contextualize_q_prompt,
    )
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    conversational_rag_chain = RunnableWithMessageHistory(
        rag_chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer",
    )

    # Invoke the RAG chain
    response = conversational_rag_chain.invoke(
        {"input": message.content},
        config={"configurable": {"session_id": ""}},
    )["answer"]

    # Stream response to the user
    msg = cl.Message(content="")
    await msg.stream_token(response)
    await msg.send()

    # retriever, client = cl.user_session.get("llm_chain")
    # print(message)
    # context = retriever.get_relevant_documents(message.content)
    #
    # context = ''.join(x.page_content for x in context)
    #
    # msg = cl.Message(content="")
    #
    # prompt_template = """Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer. and give summarized answer
    #
    # {context}
    #
    # Question: {question}
    # Helpful Answer:""".format(context=context, question=message.content)
    #
    # model = "meta-llama/llama-3-70b-instruct"
    # stream = True  # or False
    # max_tokens = 2000
    #
    # chat_completion_res = client.chat.completions.create(
    #     model=model,
    #     messages=[
    #         {
    #             "role": "system",
    #             "content": "Act like you are a helpful assistant.",
    #         },
    #         {
    #             "role": "user",
    #             "content": prompt_template,
    #         }
    #     ],
    #     stream=stream,
    #     max_tokens=max_tokens,
    # )
    # for chunk in chat_completion_res:
    #     await msg.stream_token(chunk.choices[0].delta.content or "")
    #
    # await msg.send()


if __name__ == "__main__":
    from chainlit.cli import run_chainlit

    run_chainlit(__file__)
