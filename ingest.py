import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import Language, RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

# CONFIGURATION
# Set this to the folder containing the external code you want to analyze
CODEBASE_DIR = "/home/filth/nonprofit-api" 
PERSIST_DIR = "/home/filth/nonprofit-api-rag/chroma_db"
COLLECTION_NAME = "nonprofit_api_collection"

def main():
    if not os.path.exists(CODEBASE_DIR):
        print(f"Error: The directory {CODEBASE_DIR} does not exist.")
        return

    print(f"--- Starting Codex Ingestion ---")
    print(f"Reading source files from: {CODEBASE_DIR}")

    # 1. Load files using the universally supported DirectoryLoader and TextLoader
    loader = DirectoryLoader(
        CODEBASE_DIR,
        glob="**/*.py",
        loader_cls=TextLoader
    )
    documents = loader.load()
    print(f"Successfully loaded {len(documents)} source files.")

    # 2. Split the code structurally by Python classes and functions
    splitter = RecursiveCharacterTextSplitter.from_language(
        language=Language.PYTHON, 
        chunk_size=2000, 
        chunk_overlap=200
    )
    texts = splitter.split_documents(documents)
    print(f"Split codebase into {len(texts)} individual code chunks.")

    # 3. Generate embeddings and save to the local database
    print("Computing embeddings and writing to ChromaDB...")
    embeddings = OpenAIEmbeddings()
    
    Chroma.from_documents(
        documents=texts,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=PERSIST_DIR
    )
    print(f"--- Ingestion Complete! Saved to {PERSIST_DIR} ---")

if __name__ == "__main__":
    main()
