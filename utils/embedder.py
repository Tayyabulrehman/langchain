import argparse
import os

from dotenv import load_dotenv
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_postgres import PGVector
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

CHUNK_SIZE = 500  # chunk size to create snippets
CHUNK_OVERLAP = 50  # check size to create overlap between snippets
OUTPUT_RESULT_COUNT = 5


def create_embeddings(file_path: str, role):
    # Initialize a list to store text snippets
    snippets = []
    # Initialize a CharacterTextSplitter with specified settings
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " "]
    )

    # Read the content of the file specified by file_path
    with open(file_path, "r", encoding="utf-8") as file:
        file_text = file.read()
    #
    # # Split the text into snippets using the specified settings
    snippets = text_splitter.split_text(file_text)
    # print(len(snippets))
    embeddings = HuggingFaceEmbeddings(model_name=os.getenv("EMBEDDING_MODEL"))
    data = {"manager": True if role == "manager" else False,
            "employee": True if role == "employee" else False}
    docs = [Document(page_content=x, metadata=data) for x in snippets]

    vector_store = PGVector(
        embeddings=embeddings,
        collection_name="law-index-v3",
        connection=os.getenv("connection"),
        use_jsonb=True,
    )
    vector_store.add_documents(docs)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Embeded doc")
    parser.add_argument('file_path', type=str)
    parser.add_argument('role', type=str)
    args = parser.parse_args()
    create_embeddings(args.file_path, args.role)
