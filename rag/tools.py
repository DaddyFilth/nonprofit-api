import os
from langchain_core.tools.retriever import create_retriever_tool
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

# 1. Initialize your embeddings
embeddings = OpenAIEmbeddings()

# 2. Re-connect to your existing ChromaDB collection
# We'll use the chroma_db directory at the project root
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
persist_directory = os.path.join(project_root, "chroma_db")

# Inside tools.py
vectorstore = Chroma(
    collection_name="nonprofit_api_collection",
    persist_directory="/home/filth/nonprofit-api-rag/chroma_db",
    embedding_function=embeddings
)
# 3. Create the retriever
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

# 4. Define the tool
retriever_tool = create_retriever_tool(
    retriever,
    name="nonprofit_api_search",
    description="Search the nonprofit-api codebase for documentation, function logic, or API endpoints."
)

tools = [retriever_tool]
