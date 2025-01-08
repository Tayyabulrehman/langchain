import os

from dotenv import load_dotenv
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

load_dotenv()
embeddings = HuggingFaceEmbeddings(model_name=os.getenv("EMBEDDING_MODEL"))


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
