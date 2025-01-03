import os

from dotenv import load_dotenv
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
load_dotenv()
embeddings = HuggingFaceEmbeddings(model_name=os.getenv("EMBEDDING_MODEL"))

vector_store = FAISS.load_local("law_index", embeddings, allow_dangerous_deserialization=True)


print("")
