import os
import warnings
from dotenv import load_dotenv
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pinecone import Pinecone

# === Disable LangChain Tracing & CodeCarbon ===
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["LANGCHAIN_PROJECT"] = ""
os.environ["LANGCHAIN_ENDPOINT"] = ""
os.environ["LANGCHAIN_API_KEY"] = ""
os.environ["CODECARBON_LOG_LEVEL"] = "error"
warnings.filterwarnings("ignore", message=".*CodeCarbonCallback.*")

# === Load environment variables ===
load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
PINECONE_NAMESPACE = os.getenv("PINECONE_NAMESPACE", "")

# === Initialize Pinecone ===
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)

# === Text splitter (LangChain orchestration) ===
def split_text(content: str, chunk_size: int = 500, overlap: int = 50):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=overlap
    )
    return splitter.split_text(content)

# === Create embeddings using LangChain ===
def create_embeddings(file_path: str, user_id: str):
    # Try reading the file in multiple encodings
    encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
    file_text = None
    for encoding in encodings:
        try:
            with open(file_path, "r", encoding=encoding) as f:
                file_text = f.read()
            print(f"✅ Successfully read file with {encoding} encoding")
            break
        except UnicodeDecodeError:
            continue
    if not file_text:
        raise ValueError(f"❌ Could not decode file {file_path}")

    # Split text
    snippets = split_text(file_text)
    print(f"🧩 Split into {len(snippets)} chunks")

    # Create LangChain embeddings
    embeddings = SentenceTransformerEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # Create LangChain vectorstore (Pinecone)
    vectorstore = PineconeVectorStore(
        index_name=PINECONE_INDEX_NAME,
        embedding=embeddings,
        namespace=PINECONE_NAMESPACE
    )

    # Prepare metadata
    metadatas = [{"file_path": file_path, "user_id": user_id, "chunk_index": i} for i in range(len(snippets))]

    # Upsert using LangChain orchestrator
    print(f"🚀 Uploading embeddings to Pinecone...")
    vectorstore.add_texts(snippets, metadatas=metadatas)
    print(f"✅ Successfully embedded {len(snippets)} documents for user {user_id}")


if __name__ == "__main__":
    create_embeddings("../sample.txt", "1")
