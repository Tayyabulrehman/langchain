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


def load_pdfs(pdf_files: list[str]) -> list:
    """
    Load PDF files and return documents
    """
    docs = []
    for pdf_file in pdf_files:
        loader = PyPDFLoader(file_path=pdf_file)
        docs.extend(loader.load())
    return docs


# ----------------------------
# Text Splitter
# ----------------------------
def split_documents(documents: list, chunk_size: int = 500, chunk_overlap: int = 100) -> list:
    """
    Split documents into smaller chunks
    """
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return text_splitter.split_documents(documents)


# ----------------------------
# Embeddings for PDFs
# ----------------------------
def embed_pdfs(pdf_files: list[str]):
    """
    Load PDFs, split them, generate embeddings using OpenAI text-embedding-3-small, and store in Pinecone
    """
    # Load PDFs
    pdf_docs = load_pdfs(pdf_files)

    # Split documents
    splitted_docs = split_documents(pdf_docs)

    # Create embeddings
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    # Create vector store and add documents
    vectorstore = PineconeVectorStore(embedding=embeddings, index=index)
    vectorstore.add_documents(documents=splitted_docs)

    print(f"Added {len(splitted_docs)} document chunks to Pinecone index '{index_name}'.")

pdf_files = ["company_tech.pdf",]
embed_pdfs(pdf_files)
