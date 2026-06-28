import os
from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.document_loaders.parsers import LanguageParser
from langchain_text_splitters import Language
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

def index_project():
    # Define project root (one level up from this file)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    persist_directory = os.path.join(project_root, "chroma_db")

    print(f"Indexing codebase at: {project_root}")

    # 1. Parse code files (Python)
    loader = GenericLoader.from_filesystem(
        project_root,
        glob="**/*",
        suffixes=[".py"],
        exclude=["venv", "__pycache__", "nonprofit-api-local"],
        parser=LanguageParser(language=Language.PYTHON, parser_threshold=500)
    )
    docs = loader.load()
    print(f"Loaded {len(docs)} documents.")

    # 2. Embed & store in ChromaDB
    print("Generating embeddings and storing in ChromaDB...")
    Chroma.from_documents(
        documents=docs,
        embedding=OpenAIEmbeddings(),
        persist_directory=persist_directory,
        collection_name="nonprofit_codebase"
    )
    print(f"Indexing complete. Database stored in {persist_directory}")

if __name__ == "__main__":
    index_project()
