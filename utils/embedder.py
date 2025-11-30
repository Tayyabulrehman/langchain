import os
from xml.dom.minidom import Document

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Pinecone as LangChainPinecone
# from pinecone import Pinecone as pc
from pypdf import PdfReader

load_dotenv()

PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# # pc = Pinecone(api_key=PINECONE_API_KEY)
# index_name = "rag"
# index = pc.Index(index_name)


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
# def embed_pdfs(pdf_files: list[str]):
#     """
#     Load PDFs, split them, generate embeddings using OpenAI text-embedding-3-small, and store in Pinecone
#     """
#     # Load PDFs
#     pdf_docs = load_pdfs(pdf_files)
#
#     # Split documents
#     splitted_docs = split_documents(pdf_docs)
#
#     # Create embeddings
#     embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
#
#     # Create vector store and add documents
#     vectorstore = PineconeVectorStore(embedding=embeddings, index=index)
#     vectorstore.add_documents(documents=splitted_docs)
#
#     print(f"Added {len(splitted_docs)} document chunks to Pinecone index '{index_name}'.")
from langchain.schema import Document
from langchain_pinecone import PineconeVectorStore

def embed_pdfs(pdf_files: list[str], metadata: dict = None):
    """
    Load PDFs, split them, generate embeddings using OpenAI text-embedding-3-small,
    attach metadata, and store in Pinecone.

    Args:
        pdf_files (list[str]): List of PDF file paths
        metadata (dict, optional): Metadata to attach to all document chunks
    """
    all_docs = []

    # 1️⃣ Load PDFs and split into chunks
    for pdf_file in pdf_files:
        pdf_reader = PdfReader(pdf_file)
        text = "".join([page.extract_text() or "" for page in pdf_reader.pages])

        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=50)
        chunks = splitter.split_text(text)

        # Convert each chunk into a Document object with metadata
        docs_with_meta = [
            Document(
                page_content=chunk,
                metadata={"source": pdf_file, **(metadata or {})}
            )
            for chunk in chunks
        ]
        all_docs.extend(docs_with_meta)

    # 2️⃣ Create embeddings
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    # 3️⃣ Add documents to Pinecone vector store (Pinecone v3+)
    vectorstore = PineconeVectorStore.from_documents(
        documents=all_docs,
        embedding=embeddings,
        index_name=os.environ.get("PINECONE_INDEX_NAME"),
    )

    print(f"Added {len(all_docs)} document chunks to Pinecone index '{os.environ.get('PINECONE_INDEX_NAME')}'.")
    return vectorstore


from pinecone import Pinecone

def delete_docs_by_metadata(index_name: str, metadata: dict,):
    """
    Delete documents from Pinecone index based on metadata filter.

    Args:
        index_name (str): Name of the Pinecone index
        metadata (dict): Metadata filter, e.g., {"project": {"$eq": "voiceMe"}}
        api_key (str): Pinecone API key
        environment (str): Pinecone environment
    """
    # Initialize Pinecone client
    client = Pinecone(api_key=os.getenv("PINECONE_API_KEY"), environment=os.getenv("PINECONE_ENVIRONMENT"))

    # Connect to the index
    index = client.Index(index_name)

    # Delete vectors matching the metadata filter
    index.delete(filter=metadata)

    print(f"Deleted all documents from index '{index_name}' matching metadata: {metadata}")
# pdf_files = ["re.pdf",]
# embed_pdfs(pdf_files)
