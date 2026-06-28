from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
try:
    from .tools import tools
except ImportError:
    from tools import tools

# Now this will work because 'tools' is defined
llm = ChatOpenAI(model="gpt-4o", temperature=0)
agent_executor = create_react_agent(llm, tools)
