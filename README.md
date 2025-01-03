# RAG App with Chainlit

This project is a **Retrieval-Augmented Generation (RAG)** application built using **Chainlit**. The app combines the power of large language models (LLMs) and a vector database to provide highly accurate responses by retrieving and leveraging relevant context from a knowledge base.

---

## **Features**
- **Document Ingestion:** Upload documents and convert them into embeddings.
- **Vector Database Integration:** Use Pincone or other vector databases to store and retrieve document embeddings.
- **Contextual Responses:** Combine LLM-generated answers with retrieved context for accurate and grounded outputs.
- **Chainlit Frontend:** User-friendly interface for seamless interaction with the model.

---

## **Project Structure**

```plaintext
law-ai/
├── app.py                # Main entry point for the Chainlit application
├── requirements.txt      # Python dependencies
├── .chainlit/            # Chainlit-specific configuration (if required)
├── data/
│       # Vector database (e.g., FAISS or Milvus)
├── utils/
│   ├── data_loader.py    # Functions for loading documents
│   ├── embedder.py       # Embedding generation logic
│   ├── retriever.py      # Logic for querying the vector database
│   └── response_gen.py   # Functions for generating responses
├── models/     llm_interface.py  # Interface for interacting with LLM (e.g., OpenAI, Hugging Face)
└── README.md             # Documentation for the project
```

---

## **Getting Started**

### **1. Prerequisites**
- Python 3.8+
- pip or pipenv for package management

### **2. Installation**

1. Clone the repository:
   ```bash
   git clone https://github.com/astutesoftwares/law.ai.git
   cd law_ai
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
    - Create a `.env` file and add keys for your LLM or vector database API (e.g., OpenAI API Key):
     ```plaintext
    connection =postgresql+psycopg://postgres:admin@localhost:5433/test
    collection_name=my_docs
    EMBEDDING_MODEL =all-MiniLM-L6-v2
    CHAINLIT_AUTH_SECRET ="your secret key"   generate using openssl
    ```

4. **Vector Db setup:**
    1. Install pg_vector using [pgvector GitHub](https://github.com/pgvector/pgvector).
    2. Create Vector Extension using:
       ```sql
       CREATE EXTENSION vector;
       ```

5. **LLM Setup**
    1. Tunnel LLM API through this command:
       ```bash
       ssh -L 8080:localhost:11434 astutesoftwares@194.247.183.133
       ```

---

### **3. Running the App**
Start the Chainlit application:
```bash
chainlit run app.py
```

Access the app at `http://localhost:8000`.

---

## **Usage**

### **1. Upload Documents**
Place documents (PDF, text files, etc.) in the `data/documents/raw` directory.
Clean them one by one using this command:
```bash
python utils/data_loader.py data/raw/path_to_your_file data/cleaned/path_destination_file
```


### **2. Generate Embeddings**
Run the embedding generation script to process the documents:
```bash
python utils/embedder.py data/cleaned/path_to_your_file --role
```

### **3. Query the App**
- Ask questions in the Chainlit interface. The app retrieves relevant documents from the vector database and uses the LLM to provide a grounded response.

---


## **Contact**
For questions or feedback, please contact [tayyab@astutesoftwares.com, ashar@astutessoftwares.com].

