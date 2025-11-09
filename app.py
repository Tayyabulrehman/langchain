import os

from operator import index

from dotenv import load_dotenv
from pinecone import Pinecone




from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain.memory import ConversationBufferMemory
from langchain_community.embeddings import HuggingFaceEmbeddings, SentenceTransformerEmbeddings, OpenAIEmbeddings
from langchain_core.prompts import PromptTemplate, MessagesPlaceholder
from langchain_community.chat_message_histories import ChatMessageHistory


import chainlit as cl
from langchain_pinecone import PineconeVectorStore


from utils.auth import authenticate
from utils.wraper import CustomAPIModel, get_response, ChatGPTModel

load_dotenv()

PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

pc = Pinecone(api_key=PINECONE_API_KEY)
index_name = "rag"
index = pc.Index(index_name)


from langchain.chains import RetrievalQA
llm = ChatGPTModel(model_name="gpt-4-turbo")
# Initialize Pinecone vector store
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = PineconeVectorStore(index=index, embedding=embeddings)
retriever = vectorstore.as_retriever(search_type="similarity")

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
    # context = results = vector_store.similarity_search(message.content, k=10,
    #                                                    )
    msg = cl.Message(content="")
    # if context:
    #     context = ''.join(x.page_content for x in context)
    #
    #     msg = cl.Message(content="")

    prompt_template = """You are an assistant for question-answering tasks.
    Use the following documents to answer the question.
    If you don't know the answer, just say that you don't know.
    Use three sentences maximum and keep the answer concise:
    Question: {question}
    Answer:
    """.format(question=message.content)
    qa = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever, return_source_documents=True)
    # Query the model
    # prompt = "AI Agents vs. Agentic AI"
    result = qa({"query": prompt_template})
    response=result.get("result")
    await msg.stream_token(response or "")
    await msg.send()


if __name__ == "__main__":
    from chainlit.cli import run_chainlit

    run_chainlit(__file__)
