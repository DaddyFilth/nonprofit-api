import os
from git import Repo
from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.document_loaders.parsers import LanguageParser
from langchain_text_splitters import Language
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

# 1. Clone the repo
repo_path = "./nonprofit-api-local"
if not os.path.exists(repo_path):
    Repo.clone_from("https://github.com/daddyfilth/nonprofit-api", repo_path)

# 2. Parse code files (Python)
loader = GenericLoader.from_filesystem(
    repo_path,
    glob="**/*",
    suffixes=[".py"],
    parser=LanguageParser(language=Language.PYTHON, parser_threshold=500)
)
docs = loader.load()

# 3. Embed & store in ChromaDB
vectorstore = Chroma.from_documents(
    documents=docs,
    embedding=OpenAIEmbeddings(),
    persist_directory="./chroma_db"
)

# 4. Initialize retriever
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

