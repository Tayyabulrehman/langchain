import os

from dotenv import load_dotenv
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

from utils.wraper import CustomAPIModel

load_dotenv()



def create_role_based_retriever(vector_store, user_role):
    filter = {}
    if user_role == "employee":
        filter = {"employee": True}
    elif user_role == "manager":
        filter = {"manager": True}
    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={
            "k": 10,
            "filter": filter
        }
    )


from langchain.vectorstores import Pinecone

import os

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
load_dotenv()

PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

pc = Pinecone(api_key=PINECONE_API_KEY)
index_name = "rag"
index = pc.Index(index_name)


from langchain.chains import RetrievalQA
llm = CustomAPIModel()
# Initialize Pinecone vector store
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = PineconeVectorStore(index=index, embedding=embeddings)
retriever = vectorstore.as_retriever(search_type="similarity")

# Set up RetrievalQA chain
qa = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever, return_source_documents=True)

# Query the model
prompt = "AI Agents vs. Agentic AI"
result = qa({"query": prompt})

print("QA Response:", result)